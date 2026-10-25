"""
Usage:
    python manage.py start_worker

Starts the RabbitMQ consumer that processes:
  - follow_user     → notifies the followed user
  - follow_post     → confirms subscription to follower
  - content_event   → fan-out to all followers of user/post
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Start the RabbitMQ worker that processes notification events'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('[Worker] Starting RabbitMQ consumer...'))
        from notifications.rabbit import start_consuming
        start_consuming()
