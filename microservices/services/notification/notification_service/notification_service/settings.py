"""
Django settings for notification_service project.
"""
from pathlib import Path
import os


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'PbnBBmmF5aDqeRQ1Pd1xEM0wUwjpiT8d52k4oaxHMXU'

DEBUG = 'True'

ALLOWED_HOSTS = ["0.0.0.0","oussama-bjm-notification.hf.space","oussama-bjm-notification2.hf.space", "127.0.0.1","localhost"]
CSRF_TRUSTED_ORIGINS = [
    "oussama-bjm-notification.hf.space",
    "oussama-bjm-notification2.hf.space",
    "0.0.0.0",
    "127.0.0.1",
    "localhost"
]
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework_simplejwt',
    'rest_framework',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'notification_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'notification_service.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'cynegcxx_notification-service',
        'USER': 'cynegcxx_admin',
        'PASSWORD': 'admin@2026',
        'HOST': '178.32.109.176',
        'PORT': '3306',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
}

# RabbitMQ configuration
RABBITMQ_HOST = '147.224.161.221'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'guest'
RABBITMQ_PASS = 'guest'
RABBITMQ_VHOST = '/'

# Queue names
QUEUE_FOLLOW_USER    = 'follow_user'
QUEUE_FOLLOW_POST    = 'follow_post'
QUEUE_UNFOLLOW_USER  = 'unfollow_user'
QUEUE_UNFOLLOW_POST  = 'unfollow_post'
QUEUE_CONTENT_EVENT  = 'content_event'
RABBITMQ_USER_EXCHANGE = 'user_events'
RABBITMQ_VEHICLE_EXCHANGE = 'vehicle_events'

