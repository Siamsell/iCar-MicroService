from django.core.management.base import BaseCommand
from django.conf import settings
import sys


class Command(BaseCommand):
    help = 'Start the RabbitMQ worker that processes notification events'

    def add_arguments(self, parser):
        parser.add_argument(
            '--queue',
            type=str,
            default='notifications',
            help='RabbitMQ queue name to consume from'
        )

    def handle(self, *args, **options):
        queue_name = options['queue']

        self.stdout.write(self.style.SUCCESS(
            f'[Worker] Starting RabbitMQ consumer for queue: {queue_name}...'
        ))

        try:
            from catalog.rabbitmq_consumer import start_user_events_consumer

            start_user_events_consumer()

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('\n[Worker] Stopped by user (CTRL+C)'))
            sys.exit(0)

        except ImportError as e:
            self.stdout.write(self.style.ERROR(
                f'[Worker] Failed to import consumer module: {e}'
            ))
            sys.exit(1)

        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'[Worker] Unexpected error: {e}'
            ))
            sys.exit(1)