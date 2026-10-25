import json
import logging
import time
import pika,sys
from django.conf import settings
from notifications.models import Notification, UserFollowUser, UserFollowPost, VehiculeModel,UserModel
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db import close_old_connections

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)


def _get_connection():
    credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASS)
    params = pika.ConnectionParameters(
        host=settings.RABBITMQ_HOST,
        port=settings.RABBITMQ_PORT,
        virtual_host=settings.RABBITMQ_VHOST,
        credentials=credentials,
        connection_attempts=3,
        retry_delay=2,
    )
    return pika.BlockingConnection(params)


# def _publish(queue_name: str, payload: dict):
#     """Open a connection, declare exchange, publish one message, close."""
#     try:
#         connection = _get_connection()
#         channel = connection.channel()
        
#         # Declare topic exchange instead of direct queue
#         exchange_name = 'notification_events'
#         channel.exchange_declare(
#             exchange=exchange_name,
#             exchange_type='topic',
#             durable=True
#         )
        
#         # Declare queue and bind to exchange
#         channel.queue_declare(queue=queue_name, durable=True)
#         channel.queue_bind(
#             exchange=exchange_name,
#             queue=queue_name,
#             routing_key=queue_name
#         )
        
#         # Publish to exchange with routing key
#         channel.basic_publish(
#             exchange=exchange_name,
#             routing_key=queue_name,
#             body=json.dumps(payload),
#             properties=pika.BasicProperties(delivery_mode=2),
#         )
#         connection.close()
#         print(f"[RabbitMQ] Published to '{queue_name}': {payload}")
#     except Exception as exc:
#         print(f"[RabbitMQ] Failed to publish to '{queue_name}': {exc}")
def _publish(routing_key: str, payload: dict):
    try:
        connection = _get_connection()
        channel = connection.channel()
        
        exchange_name = 'notification_events'
        channel.exchange_declare(exchange=exchange_name, exchange_type='topic', durable=True)

        # Declare ALL consumer queues and bind them to this routing key
        # so messages are never lost even if a consumer is offline
        consumer_queues = {
            'follow_user.events':  ['follow_user.events_local', 'follow_user.events_notification1', 'follow_user.events_notification2'],
            'follow_post.events':  ['follow_post.events_local', 'follow_post.events_notification1', 'follow_post.events_notification2'],
            'content.events':      ['content.events_local',     'content.events_notification1',     'content.events_notification2'],
        }

        for queue_name in consumer_queues.get(routing_key, []):
            channel.queue_declare(queue=queue_name, durable=True)
            channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key=routing_key)

        channel.basic_publish(
            exchange=exchange_name,
            routing_key=routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        connection.close()
        print(f"[RabbitMQ] Published '{routing_key}': {payload}")
    except Exception as exc:
        print(f"[RabbitMQ] Failed to publish '{routing_key}': {exc}")
# ──────────────────────────────────────────────────────────────────────────────
# Publishers (called from views)
# ──────────────────────────────────────────────────────────────────────────────

def publish_follow_user(follower_id: int, following_id: int, user_name=""):
    _publish('follow_user.events', {
        'event_type': 'follow_user',
        'follower_id': follower_id,
        'following_id': following_id,
        'user_name': user_name
    })

def publish_follow_post(user_id: int, post_id: int, user_name=""):
    _publish('follow_post.events', {  
        'event_type': 'follow_post',
        'user_id': user_id,
        'post_id': post_id,
        'user_name': user_name
    })

def publish_content_event(owner_user_id: int, post_id, event_type: str, title: str):
    _publish('content.events', {  
        'event_type': event_type,
        'owner_user_id': owner_user_id,
        'post_id': post_id,
        'title': title,
    })


# ──────────────────────────────────────────────────────────────────────────────
# Consumer callbacks
# ──────────────────────────────────────────────────────────────────────────────

def _handle_follow_user(ch, method, properties, body):
    try:

        close_old_connections()
        
        data = json.loads(body)
        follower_id = data['follower_id']
        following_id = data['following_id']
        user_name = data.get('user_name', '')
        
        try:
            user = UserModel.objects.get(id=follower_id)
            user_name = user.name
        except ObjectDoesNotExist:
            user_name = "User"
            


        Notification.objects.get_or_create(
            user_id=following_id,
            subject='New follower',
            message=f'{user_name} started following you.',
            post=None,
            follower_id=follower_id,
            type=Notification.Type.FOLLOW_USER 
        )
        print(f"[Worker] follow_user → notified user {following_id}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as exc:
        print(f"[Worker] follow_user error: {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)



def _handle_follow_post(ch, method, properties, body):
    try:

        close_old_connections()
        
        data = json.loads(body)
        user_id = int(data['user_id'])  # ← Convert to integer
        post_id = int(data['post_id'])  # ← Convert to integer

        # Get follower user instance
        try:
            follower = UserModel.objects.get(id=user_id)
            follower_name = follower.name
        except UserModel.DoesNotExist:
            print(f"[Worker] User {user_id} not found")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Get the post owner
        try:
            vehicle = VehiculeModel.objects.get(id=post_id)
            owner = vehicle.user  # This is already a UserModel instance
            owner_id = owner.id
        except VehiculeModel.DoesNotExist:
            print(f"[Worker] Post {post_id} not found")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # 1. Notification for the follower (confirmation)
        notification1, created1 = Notification.objects.get_or_create(
            user=follower,  # ← Pass UserModel instance, not ID
            post_id=post_id,
            type=Notification.Type.FOLLOW_POST,
            defaults={
                'subject': 'Post followed',
                'message': f'You are now following post `{vehicle.brand} {vehicle.name}`, You will receive updates.',

            }
        )
        
        if created1:
            print(f"[Worker] follow_post → confirmed to user {user_id} for post {post_id}")
        else:
            print(f"[Worker] follow_post → duplicate ignored for user {user_id}")

        # 2. Notification for the post owner (someone followed their post)
        if owner.id != user_id:
            notification2, created2 = Notification.objects.get_or_create(
                user=owner,  # ← Pass UserModel instance
                post_id=post_id,
                type=Notification.Type.FOLLOW_POST,
                defaults={
                    'subject': f'{follower_name} followed your post',
                    'message': f'{follower_name} started following your post `{vehicle.brand} {vehicle.name}`.',
                }
            )
            
            if created2:
                print(f"[Worker] follow_post → notified owner {owner.id} for post {post_id}")
            else:
                print(f"[Worker] follow_post → duplicate ignored for owner {owner.id}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as exc:
        print(f"[Worker] follow_post error: {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)




# ──────────────────────────────────────────────────────────────────────────────
# User event handlers (using CASCADE)
# ──────────────────────────────────────────────────────────────────────────────

def _handle_user_created(ch, method, properties, body):

    
    """Create user in notification service"""
    try:

        close_old_connections()
        
        message = json.loads(body)
        user_data = message.get('user')
        
        if not user_data:
            print("Missing user data")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        UserModel.objects.update_or_create(
            id=user_data['id'],
            defaults={
                'name': user_data.get('name', ''),
                'email': user_data.get('email', ''),
                'number': user_data.get('number', ''),
                'role': user_data.get('role', 'user'),
                'date_joined': user_data.get('date_joined', timezone.now())
            }
        )
        print(f"[Worker] User created/updated: {user_data['id']}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as exc:
        print(f"[Worker] user_created error: {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def _handle_user_updated(ch, method, properties, body):
    """Update user in notification service (same as create)"""
    _handle_user_created(ch, method, properties, body)


def _handle_user_deleted(ch, method, properties, body):
    """
    Handle user_deleted event.
    Deleting UserModel will CASCADE delete:
    - All notifications (user and follower)
    - All UserFollowPost records (user_id)
    - All UserFollowUser records (follower_id and following_id)
    """
    try:

        close_old_connections()
        
        message = json.loads(body)        
        user_id = message.get('user_id')
        
        if not user_id:
            user_data = message.get('user')
            if user_data:
                user_id = user_data.get('id')
        
        if not user_id:
            print("Missing user_id")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
                
        
        # Delete user - CASCADE handles everything else!
        deleted_count, _ = UserModel.objects.filter(id=user_id).delete()
        
        if deleted_count > 0:
            print(f"[Worker] User {user_id} deleted (CASCADE cleaned all related data)")
        else:
            print(f"[Worker] User {user_id} not found")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as exc:
        print(f"[Worker] user_deleted error: {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# ──────────────────────────────────────────────────────────────────────────────
# Vehicle event handlers (using CASCADE)
# ──────────────────────────────────────────────────────────────────────────────


def _handle_content_event(ch, method, properties, body):
    try:

        close_old_connections()
        
        data = json.loads(body)
        vehicule_data = data.get('vehicule_data')
        event_type = data.get('event_type', 'content_update')
        title = data.get('title', 'New Content')
        
        if not vehicule_data:
            print("Missing vehicule_data in message")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        vehicle_id = vehicule_data.get('id')
        owner_user_id = vehicule_data.get('user')
        vehicle_name = vehicule_data.get('name', '')
        vehicle_brand = vehicule_data.get('brand', '')

        if not owner_user_id:
            print("Missing user in vehicule_data")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        subject = title
        message = 'Click to view details'

        recipient_ids = set()

        # FIXED: Users who follow the owner
        user_followers = UserFollowUser.objects.filter(
            following_id=owner_user_id  # Find records where 'following' = owner
        ).values_list('follower', flat=True)  # Get the 'follower' IDs
        recipient_ids.update(user_followers)
        print(f"[Worker] Found {len(user_followers)} users following owner {owner_user_id}")

        # Users who follow the specific post
        if vehicle_id:
            post_followers = UserFollowPost.objects.filter(
                post_id=vehicle_id
            ).values_list('user', flat=True)
            recipient_ids.update(post_followers)
            print(f"[Worker] Found {len(post_followers)} users following post {vehicle_id}")

        recipient_ids.discard(owner_user_id)
        print(f"[Worker] Total recipients: {len(recipient_ids)}")

        # Create or update VehiculeModel
        try:
            user = UserModel.objects.get(id=owner_user_id)
            VehiculeModel.objects.update_or_create(
                id=vehicle_id,
                defaults={
                    'user': user,
                    'name': vehicle_name,
                    'brand': vehicle_brand
                }
            )
            print(f"[Worker] Created/Updated vehicle {vehicle_id}")
        except UserModel.DoesNotExist:
            print(f"[Worker] User {owner_user_id} not found")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        # Create notifications
        notifications = []
        for uid in recipient_ids:
            try:
                notifications.append(Notification(
                    user_id=uid,
                    subject=subject,
                    message=message,
                    post_id=vehicle_id,
                    type=Notification.Type.POST
                ))
            except Exception as e:
                print(f"[Worker] Error creating notification for user {uid}: {e}")
        
        if notifications:
            Notification.objects.bulk_create(notifications, ignore_conflicts=True)
            print(f"[Worker] → notified {len(notifications)} users")
        else:
            print(f"[Worker] No notifications to create")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as exc:
        print(f"[Worker] content_event error: {exc}")
        import traceback
        traceback.print_exc()
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def _handle_vehicle_deleted(ch, method, properties, body):
    """
    Handle vehicle_deleted event.
    Deleting VehiculeModel will CASCADE delete:
    - All notifications with this post
    - All UserFollowPost records with this post_id
    """
    try:

        close_old_connections()
        
        message = json.loads(body)
        vehicle_id = message.get('vehicle_id')
        
        if not vehicle_id:
            print("Missing vehicle_id")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        
        
        # Delete vehicle - CASCADE handles notifications and follows!
        deleted_count, _ = VehiculeModel.objects.filter(id=vehicle_id).delete()
        
        if deleted_count > 0:
            print(f"[Worker] Vehicle {vehicle_id} deleted (CASCADE cleaned all related data)")
        else:
            print(f"[Worker] Vehicle {vehicle_id} not found")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)
        
    except Exception as exc:
        print(f"[Worker] vehicle_deleted error: {exc}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


# ──────────────────────────────────────────────────────────────────────────────
# Consumer entry-point
# ──────────────────────────────────────────────────────────────────────────────
def start_consuming():
    """
    Start a blocking consumer that listens on all queues.
    Run via: python manage.py start_worker
    """

    print("=" * 50)
    print("WORKER STARTING...")
    print("=" * 50)

    
    connection = _get_connection()
    channel = connection.channel()

    # Declare topic exchange for all notification events
    notification_exchange = 'notification_events'
    channel.exchange_declare(
        exchange=notification_exchange,
        exchange_type='topic',
        durable=True
    )

    # 1. Follow User Queue
    follow_user_queue = 'follow_user.events_notification1'
    channel.queue_declare(queue=follow_user_queue, durable=True)
    channel.queue_bind(
        exchange=notification_exchange,
        queue=follow_user_queue,
        routing_key='follow_user.events'
    )
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=follow_user_queue, on_message_callback=_handle_follow_user)
    print(f"[Worker] Listening on queue: '{follow_user_queue}'")

    # 2. Follow Post Queue
    follow_post_queue = 'follow_post.events_notification1'
    channel.queue_declare(queue=follow_post_queue, durable=True)
    channel.queue_bind(
        exchange=notification_exchange,
        queue=follow_post_queue,
        routing_key='follow_post.events'
    )
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=follow_post_queue, on_message_callback=_handle_follow_post)
    print(f"[Worker] Listening on queue: '{follow_post_queue}'")

    # 3. Content Events Queue
    content_queue = 'content.events_notification1'
    channel.queue_declare(queue=content_queue, durable=True)
    channel.queue_bind(
        exchange=notification_exchange,
        queue=content_queue,
        routing_key='content.events'
    )
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=content_queue, on_message_callback=_handle_content_event)
    print(f"[Worker] Listening on queue: '{content_queue}'")

    # 4. User events exchange (keep as is)
    user_exchange_name = getattr(settings, 'RABBITMQ_USER_EXCHANGE', 'user_events')
    user_queue_name = 'notification_user_events_notification1'
    
    channel.exchange_declare(exchange=user_exchange_name, exchange_type='topic', durable=True)
    channel.queue_declare(queue=user_queue_name, durable=True)
    
    for routing_key in ['user.created', 'user.updated', 'user.deleted']:
        channel.queue_bind(exchange=user_exchange_name, queue=user_queue_name, routing_key=routing_key)
    
    time.sleep(0.5)
    
    def user_event_callback(ch, method, properties, body):
        routing_key = method.routing_key
        if routing_key == 'user.created':
            _handle_user_created(ch, method, properties, body)
        elif routing_key == 'user.updated':
            _handle_user_updated(ch, method, properties, body)
        elif routing_key == 'user.deleted':
            _handle_user_deleted(ch, method, properties, body)
        else:
            print(f"Unknown user event routing key: {routing_key}")
            ch.basic_ack(delivery_tag=method.delivery_tag)
    
    channel.basic_consume(queue=user_queue_name, on_message_callback=user_event_callback)
    print(f"[Worker] Listening on user events queue: '{user_queue_name}'")

    # 5. Vehicle events exchange (keep as is)
    vehicle_exchange_name = getattr(settings, 'RABBITMQ_VEHICLE_EXCHANGE', 'vehicle_events')
    vehicle_queue_name = 'notification_vehicle_events_notification1'
    
    channel.exchange_declare(exchange=vehicle_exchange_name, exchange_type='topic', durable=True)
    channel.queue_declare(queue=vehicle_queue_name, durable=True)
    channel.queue_bind(exchange=vehicle_exchange_name, queue=vehicle_queue_name, routing_key='vehicle.deleted')
    channel.basic_consume(queue=vehicle_queue_name, on_message_callback=_handle_vehicle_deleted)
    print(f"[Worker] Listening on vehicle events queue: '{vehicle_queue_name}'")

    print("[Worker] Waiting for messages. Press CTRL+C to stop.")
    
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()
    finally:
        connection.close()
        
        
        