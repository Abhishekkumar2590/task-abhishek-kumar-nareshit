"""
Configuration file for Flask, RabbitMQ, and Celery settings
"""
import os

# Flask Configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'development')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', True)
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///tasks.db')
DATABASE_FILE = os.getenv('DATABASE_FILE', 'tasks.db')

# RabbitMQ Configuration
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
RABBITMQ_USER = os.getenv('RABBITMQ_USER', 'guest')
RABBITMQ_PASSWORD = os.getenv('RABBITMQ_PASSWORD', 'guest')
RABBITMQ_VHOST = os.getenv('RABBITMQ_VHOST', '/')

# RabbitMQ Connection String
RABBITMQ_URL = f'amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/{RABBITMQ_VHOST}'

# Celery Configuration
# In development mode, use eager execution (synchronous) instead of RabbitMQ
USE_CELERY_EAGER = os.getenv('USE_CELERY_EAGER', FLASK_ENV == 'development')

if USE_CELERY_EAGER:
    # Development mode - synchronous execution
    CELERY_BROKER = 'memory://'
    CELERY_RESULT_BACKEND = 'cache+memory://'
    CELERY_ALWAYS_EAGER = True
    CELERY_EAGER_PROPAGATES_EXCEPTIONS = True
else:
    # Production mode - use RabbitMQ
    CELERY_BROKER = RABBITMQ_URL
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'rpc://')

# Queue Configuration
QUEUE_NAME = os.getenv('QUEUE_NAME', 'item_queue')
EXCHANGE_NAME = os.getenv('EXCHANGE_NAME', 'item_exchange')
ROUTING_KEY = os.getenv('ROUTING_KEY', 'item_task')
