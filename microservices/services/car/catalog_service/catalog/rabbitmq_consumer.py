import json
import logging
import sys
import time
import pika
from django.conf import settings
from django.utils import timezone
from .models import UserModel
from django.db import close_old_connections

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True
)

logger = logging.getLogger(__name__)


def handle_user_created(user_data):
    """
    Handle user.created event - add user to local database
    """

    
    user_id = user_data.get('id')
    
    if not user_id:
        print("Cannot create user: missing user_id")
        return None
    
    try:
        close_old_connections()
        
        user, created = UserModel.objects.get_or_create(
            id=user_id,
            defaults={
                'name': user_data.get('name', ''),
                'email': user_data.get('email', ''),
                'number': user_data.get('number', ''),
                'role': user_data.get('role', 'user'),
                'date_joined': user_data.get('date_joined', timezone.now())
            }
        )
        
        if created:
            print(f"User created: {user_id} - {user.name}")
        else:
            print(f"User already exists: {user_id}")
        
        return user
        
    except Exception as e:
        print(f"❌ Failed to create user {user_id}: {e}")
        return None


def handle_user_updated(user_data):
    """
    Handle user.updated event - update user in local database
    """
    user_id = user_data.get('id')
    
    if not user_id:
        print("Cannot update user: missing user_id")
        return None
    
    try:

        close_old_connections()
        
        user = UserModel.objects.filter(id=user_id).first()
        
        if user:
            # Update fields
            updated = False
            if 'name' in user_data and user.name != user_data['name']:
                user.name = user_data['name']
                updated = True
            if 'email' in user_data and user.email != user_data['email']:
                user.email = user_data['email']
                updated = True
            if 'number' in user_data and user.number != user_data['number']:
                user.number = user_data['number']
                updated = True
            if 'role' in user_data and user.role != user_data['role']:
                user.role = user_data['role']
                updated = True
            
            if updated:
                user.save()
                print(f"🔄 User updated: {user_id} - {user.name}")
            else:
                print(f"📋 No changes for user: {user_id}")
        else:
            # User doesn't exist
            print(f"⚠️ User {user_id} not found for update, creating instead")
            return None
        
        return user
        
    except Exception as e:
        print(f"❌ Failed to update user {user_id}: {e}")
        return None


def handle_user_deleted(user_id):
    """
    Handle user.deleted event - delete user from local database
    CASCADE will automatically delete all vehicles!
    """
    if not user_id:
        print("Cannot delete user: missing user_id")
        return False
    
    try:
        close_old_connections() 
        
        # Delete from UserModel - THIS WILL CASCADE DELETE ALL VEHICLES!
        deleted_count, _ = UserModel.objects.filter(id=user_id).delete()
        
        if deleted_count > 0:
            print(f"✅ User deleted: {user_id} (all vehicles deleted via CASCADE)")
        else:
            print(f"⚠️ User not found: {user_id}")
        
        return deleted_count > 0
        
    except Exception as e:
        print(f"❌ Failed to delete user {user_id}: {e}")
        return False


def start_user_events_consumer():

    try:
        credentials = pika.PlainCredentials(
            settings.RABBITMQ_USER,
            settings.RABBITMQ_PASS
        )
        params = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            virtual_host=settings.RABBITMQ_VHOST,
            credentials=credentials,
            connection_attempts=5,
            retry_delay=3,
        )
        
        
        print("connect rabbitmq success")
        
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        # Declare exchange (must match auth service)
        exchange_name = settings.RABBITMQ_USER_EXCHANGE
        channel.exchange_declare(
            exchange=exchange_name,
            exchange_type='topic',
            durable=True
        )
        
        # Declare queue for catalog service
        queue_name = 'catalog_user_events_car1'
        channel.queue_declare(queue=queue_name, durable=True)
        
        # Bind to user events
        channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name,
            routing_key='user.created'
        )
        channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name,
            routing_key='user.updated'
        )
        channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name,
            routing_key='user.deleted'
        )

        time.sleep(0.5)
        
        print(f"Catalog service consumer started. Listening on queue: {queue_name}")
        
        def callback(ch, method, properties, body):
            try:
                message = json.loads(body)
                event_type = message.get('event_type')
                routing_key = method.routing_key
                
                print(f"📨 Received: {routing_key}")
                
                # Handle user.created
                if event_type == 'user_created' or routing_key == 'user.created':
                    user_data = message.get('user')
                    if user_data:
                        handle_user_created(user_data)
                    else:
                        print("Missing user data")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                
                # Handle user.updated
                elif event_type == 'user_updated' or routing_key == 'user.updated':
                    user_data = message.get('user')
                    if user_data:
                        handle_user_updated(user_data)
                    else:
                        print("Missing user data")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                
                # Handle user.deleted
                elif event_type == 'user_deleted' or routing_key == 'user.deleted':
                    user_id = message.get('user_id')
                    if user_id:
                        handle_user_deleted(user_id)
                    else:
                        print("Missing user_id")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                
                # Unknown event
                else:
                    print(f"⚠️ Unknown event: {routing_key}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    
            except Exception as e:
                print(f"❌ Error: {e}", exc_info=True)
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        
        print("✅ Consumer started. Waiting for messages...")
        channel.start_consuming()
        
    except KeyboardInterrupt:
        print("🛑 Consumer stopped")
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        raise
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()