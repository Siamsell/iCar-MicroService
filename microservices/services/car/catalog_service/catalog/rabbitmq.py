import json
import logging
import pika
from django.conf import settings

logger = logging.getLogger(__name__)

def _get_connection():
    """Create RabbitMQ connection (same pattern as notification service)"""
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
    return pika.BlockingConnection(params)

def publish_content_event(vehicule_data, event_type: str, title: str):
    try:
        connection = _get_connection()
        channel = connection.channel()

        exchange_name = 'notification_events'
        channel.exchange_declare(exchange=exchange_name, exchange_type='topic', durable=True)

        # Declare ALL possible consumer queues (important!)
        all_content_queues = [
            'content.events',                    # Local
            'content.events_notification1',      # Server instance 1
            'content.events_notification2',      # Server instance 2
        ]
        
        for queue_name in all_content_queues:
            channel.queue_declare(queue=queue_name, durable=True)
            channel.queue_bind(exchange=exchange_name, queue=queue_name, routing_key='content.events')

        payload = {
            'vehicule_data': vehicule_data,
            'event_type': event_type,
            'title': title,
        }

        channel.basic_publish(
            exchange=exchange_name,
            routing_key='content.events',
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),
        )

        connection.close()
        print(f"[RabbitMQ] Published content event: {payload}")
        return True

    except Exception as exc:
        print(f"[RabbitMQ] Failed to publish content event: {exc}")
        return False

        
def publish_vehicle_deleted(vehicle_id, owner_user_id, vehicle_name):
    """
    Publish vehicle deletion event to RabbitMQ
    Notification service will clean up follow relationships
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
        
        # Declare exchange for vehicle events
        exchange_name = getattr(settings, 'RABBITMQ_VEHICLE_EXCHANGE', 'vehicle_events')
        channel.exchange_declare(
            exchange=exchange_name,
            exchange_type='topic',
            durable=True
        )
        
        message = {
            'event_type': 'vehicle_deleted',
            'vehicle_id': vehicle_id,
            'owner_user_id': owner_user_id,
            'vehicle_name': vehicle_name,
        }
        
        channel.basic_publish(
            exchange=exchange_name,
            routing_key='vehicle.deleted',
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2)
        )
        
        connection.close()
        print(f"Published vehicle_deleted event for vehicle {vehicle_id}")
        return True
        
    except Exception as e:
        print(f"Failed to publish vehicle_deleted event: {e}")
        return False