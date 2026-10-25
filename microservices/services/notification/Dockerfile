FROM python:3.10-slim

WORKDIR /notification_service

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

RUN pip install Django djangorestframework djangorestframework-simplejwt django-cors-headers Pillow pika pymysql -q 

COPY notification_service/ . 

EXPOSE 7860

# Create startup script - FIXED QUOTES
RUN echo '#!/bin/bash' > /start.sh && \
    echo 'echo "=== Starting Notification Service ==="' >> /start.sh && \
    echo '' >> /start.sh && \
    echo '# Run migrations' >> /start.sh && \
    echo 'python manage.py migrate --noinput' >> /start.sh && \
    echo '' >> /start.sh && \
    echo '# Start worker with output to console' >> /start.sh && \
    echo 'python manage.py start_worker 2>&1 &' >> /start.sh && \
    echo 'WORKER_PID=$!' >> /start.sh && \
    echo 'echo "Worker started with PID: $WORKER_PID"' >> /start.sh && \
    echo '' >> /start.sh && \
    echo '# Wait 3 seconds and check if worker is still running' >> /start.sh && \
    echo 'sleep 3' >> /start.sh && \
    echo 'if kill -0 $WORKER_PID 2>/dev/null; then' >> /start.sh && \
    echo '    echo "Worker is running"' >> /start.sh && \
    echo 'else' >> /start.sh && \
    echo '    echo "ERROR: Worker crashed immediately!"' >> /start.sh && \
    echo 'fi' >> /start.sh && \
    echo '' >> /start.sh && \
    echo '# Start Django server' >> /start.sh && \
    echo 'python manage.py runserver 0.0.0.0:7860' >> /start.sh

RUN chmod +x /start.sh

CMD ["/start.sh"]