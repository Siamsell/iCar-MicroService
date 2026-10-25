import json
import logging
import pika
from django.conf import settings
from datetime import datetime

logger = logging.getLogger(__name__)

def publish_user_created(user):
    """
    Publish user creation event to RabbitMQ
    Other services (catalog, notification) will consume this to create local user records
    """
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
            connection_attempts=3,
            retry_delay=2,
        )
        
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        # Declare exchange for user events
        exchange_name = getattr(settings, 'RABBITMQ_USER_EXCHANGE', 'user_events')
        channel.exchange_declare(
            exchange=exchange_name,
            exchange_type='topic',
            durable=True
        )
        
        message = {
            'event_type': 'user_created',
            'user': user,
            'timestamp': str(datetime.now())
        }
        
        channel.basic_publish(
            exchange=exchange_name,
            routing_key='user.created',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent message
                content_type='application/json'
            )
        )
        
        connection.close()
        print(f"✅ Published user_created event for user {user['id']} ({user['email']})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to publish user_created event: {e}")
        return False


def publish_user_updated(user):
    """
    Publish user update event to RabbitMQ
    Other services will update their local user records
    """
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
            connection_attempts=3,
            retry_delay=2,
        )
        
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        # Declare exchange for user events
        exchange_name = getattr(settings, 'RABBITMQ_USER_EXCHANGE', 'user_events')
        channel.exchange_declare(
            exchange=exchange_name,
            exchange_type='topic',
            durable=True
        )
        
        message = {
            'event_type': 'user_updated',
            'user': user,
            'timestamp': str(datetime.now())
        }
        
        channel.basic_publish(
            exchange=exchange_name,
            routing_key='user.updated',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent message
                content_type='application/json'
            )
        )
        
        connection.close()
        print(f"✅ Published user_updated event for user {user.id} ({user.email})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to publish user_updated event: {e}")
        return False


def publish_user_deleted(user_id, user_email, user_name):
    """
    Publish user deletion event to RabbitMQ
    Other services will delete their local user records
    """
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
            connection_attempts=3,
            retry_delay=2,
        )
        
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        
        # Declare exchange for user events
        exchange_name = getattr(settings, 'RABBITMQ_USER_EXCHANGE', 'user_events')
        channel.exchange_declare(
            exchange=exchange_name,
            exchange_type='topic',
            durable=True
        )
        
        message = {
            'event_type': 'user_deleted',
            'user_id': user_id,
            'user_email': user_email,
            'user_name': user_name,
            'timestamp': str(datetime.now())
        }
        
        channel.basic_publish(
            exchange=exchange_name,
            routing_key='user.deleted',
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Persistent message
                content_type='application/json'
            )
        )
        
        connection.close()
        print(f"✅ Published user_deleted event for user {user_id} ({user_email})")
        return True
        
    except Exception as e:
        print(f"❌ Failed to publish user_deleted event: {e}")
        return False