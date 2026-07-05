"""
Celery Worker - Consumes messages from RabbitMQ and processes them
This worker is designed to work with raw JSON payloads without Flask-Celery bindings
"""
from celery import Celery
import json
import logging
from config import (
    CELERY_BROKER,
    CELERY_RESULT_BACKEND,
    QUEUE_NAME,
    EXCHANGE_NAME,
    ROUTING_KEY,
    USE_CELERY_EAGER,
    FLASK_ENV
)
from database import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Celery app
app = Celery('item_processor')
app.conf.broker_url = CELERY_BROKER
app.conf.result_backend = CELERY_RESULT_BACKEND

# Configure queue and exchange
app.conf.task_queues = {
    QUEUE_NAME: {
        'exchange': EXCHANGE_NAME,
        'routing_key': ROUTING_KEY,
    }
}

app.conf.task_default_exchange = EXCHANGE_NAME
app.conf.task_default_routing_key = ROUTING_KEY

# Use solo pool to avoid Windows multiprocessing issues
app.conf.worker_pool = 'solo'
app.conf.worker_prefetch_multiplier = 1

# Development mode configuration
if USE_CELERY_EAGER:
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True
    logger.info("Celery configured in EAGER mode (development)")


@app.task(name='process_item', bind=True)
def process_item(self, payload):
    """
    Process item task - consumes raw JSON payload and updates database status
    
    Args:
        payload: Raw JSON payload (dict) containing item information
        Example: {"item": "book"}
    """
    try:
        logger.info(f"Processing task with payload: {payload}")
        
        # Handle both dict and JSON string payloads
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload
        
        # Extract item from payload
        item = data.get('item')
        
        if not item:
            logger.error(f"Invalid payload - missing 'item' field: {payload}")
            return {
                'status': 'failed',
                'message': 'Invalid payload - missing item field',
                'payload': payload
            }
        
        # Update database status to completed
        success = db.update_item_status(item, 'completed')
        
        if success:
            logger.info(f"Successfully updated item '{item}' status to completed")
            return {
                'status': 'success',
                'message': f"Item '{item}' status updated to completed",
                'item': item
            }
        else:
            logger.warning(f"No pending item found with name '{item}'")
            return {
                'status': 'no_item_found',
                'message': f"No pending item found with name '{item}'",
                'item': item
            }
    
    except Exception as e:
        logger.error(f"Error processing task: {str(e)}")
        return {
            'status': 'error',
            'message': str(e),
            'payload': payload
        }


if __name__ == '__main__':
    logger.info("Starting Celery worker...")
    logger.info(f"Broker: {CELERY_BROKER}")
    logger.info(f"Queue: {QUEUE_NAME}")
    logger.info(f"Exchange: {EXCHANGE_NAME}")
    app.worker_main()
