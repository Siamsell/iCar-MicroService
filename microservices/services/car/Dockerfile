FROM python:3.10-slim

WORKDIR /catalog_service

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

RUN pip install Django djangorestframework djangorestframework-simplejwt django-cors-headers Pillow pika pymysql -q 

COPY catalog_service/ . 

EXPOSE 7860

CMD ["sh", "-c", "\
python manage.py migrate --noinput && \
python manage.py consume_user_events & \
python manage.py runserver 0.0.0.0:7860"]