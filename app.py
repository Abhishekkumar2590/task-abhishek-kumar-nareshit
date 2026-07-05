"""
Flask Application with two endpoints:
1. Producer - accepts items and sends to RabbitMQ
2. Concurrent Requests - makes multiple concurrent GET requests using threading
"""
from flask import Flask, request, jsonify, send_from_directory
import json
import logging
import time
import requests
import threading
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import (
    FLASK_ENV,
    FLASK_DEBUG,
    SECRET_KEY,
    RABBITMQ_URL,
    QUEUE_NAME,
    EXCHANGE_NAME,
    ROUTING_KEY,
    USE_CELERY_EAGER
)
from database import db
try:
    import pika
    PIKA_AVAILABLE = True
except ImportError:
    PIKA_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')
app.config['ENV'] = FLASK_ENV
app.config['DEBUG'] = FLASK_DEBUG
app.config['SECRET_KEY'] = SECRET_KEY


def send_to_rabbitmq(payload):
    """
    Send message to RabbitMQ or use Celery task in development mode
    
    Args:
        payload: Dictionary to be sent as JSON to RabbitMQ
    
    Returns:
        bool: True if successful, False otherwise
    """
    # In development mode, use Celery task directly
    if USE_CELERY_EAGER:
        try:
            from worker import process_item
            process_item.apply_async(args=[payload])
            logger.info(f"Task queued (eager mode): {json.dumps(payload)}")
            return True
        except Exception as e:
            logger.error(f"Error queueing task: {str(e)}")
            return False
    
    # In production mode, use RabbitMQ
    if not PIKA_AVAILABLE:
        logger.error("pika is not installed")
        return False
    
    try:
        # Create RabbitMQ connection
        credentials = pika.PlainCredentials('guest', 'guest')
        parameters = pika.ConnectionParameters(
            host='localhost',
            port=5672,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        
        # Declare exchange
        channel.exchange_declare(
            exchange=EXCHANGE_NAME,
            exchange_type='direct',
            durable=True
        )
        
        # Declare queue
        channel.queue_declare(
            queue=QUEUE_NAME,
            durable=True
        )
        
        # Bind queue to exchange
        channel.queue_bind(
            exchange=EXCHANGE_NAME,
            queue=QUEUE_NAME,
            routing_key=ROUTING_KEY
        )
        
        # Publish message
        message = json.dumps(payload)
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=ROUTING_KEY,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
                content_type='application/json'
            )
        )
        
        logger.info(f"Message sent to RabbitMQ: {message}")
        connection.close()
        return True
    
    except Exception as e:
        logger.error(f"Error sending message to RabbitMQ: {str(e)}")
        logger.info(f"Falling back to database queue for: {json.dumps(payload)}")
        return False


@app.route('/api/items', methods=['POST'])
def create_item():
    """
    Producer endpoint - Accepts item and sends to RabbitMQ
    
    Request:
        POST /api/items
        Content-Type: application/json
        Body: {"item": "book"}
    
    Response:
        202 Accepted (no body required)
    """
    try:
        # Get JSON data
        if not request.is_json:
            return jsonify({'error': 'Request must be application/json'}), 400
        
        data = request.get_json()
        
        # Validate item parameter
        if 'item' not in data or not data['item']:
            return jsonify({'error': 'item parameter is required'}), 400
        
        item = data['item']
        
        # Insert into database with status=pending
        item_id = db.insert_item(item)
        logger.info(f"Item inserted into database: id={item_id}, item={item}, status=pending")
        
        # Prepare payload for RabbitMQ
        payload = {'item': item}
        
        # Send to RabbitMQ
        if send_to_rabbitmq(payload):
            logger.info(f"Item {item} sent to RabbitMQ successfully")
            return '', 202  # 202 Accepted
        else:
            logger.warning(f"Failed to send item {item} to RabbitMQ, but it was saved to database")
            # Still return 202 since the item was saved to database
            return '', 202
    
    except Exception as e:
        logger.error(f"Error in create_item endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/concurrent-requests', methods=['GET'])
def concurrent_requests():
    """
    Endpoint to make concurrent GET requests using threading
    
    Request:
        GET /api/concurrent-requests?delay_value=2
    
    Query Parameters:
        delay_value: Integer value for delay (1, 2, 3, etc.)
    
    Response:
        200 OK
        Body: {"time_taken": 5.35}
    """
    try:
        # Get delay_value from query parameters
        delay_value = request.args.get('delay_value', '1')
        
        # Validate delay_value is an integer
        try:
            delay_value = int(delay_value)
        except ValueError:
            return jsonify({'error': 'delay_value must be an integer'}), 400
        
        # URL to request
        base_url = f'https://httpbin.org/delay/{delay_value}'
        
        logger.info(f"Starting concurrent requests with delay_value={delay_value}")
        start_time = time.time()
        
        # Function to make a single request
        def make_request(url, request_num):
            try:
                logger.info(f"Request {request_num} started")
                response = requests.get(url, timeout=60)
                logger.info(f"Request {request_num} completed with status {response.status_code}")
                return {
                    'request_num': request_num,
                    'status_code': response.status_code,
                    'success': True
                }
            except requests.exceptions.RequestException as e:
                logger.error(f"Request {request_num} failed: {str(e)}")
                return {
                    'request_num': request_num,
                    'error': str(e),
                    'success': False
                }
        
        # Make 5 concurrent requests using ThreadPoolExecutor
        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_request, base_url, i+1)
                for i in range(5)
            ]
            
            # Wait for all requests to complete
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        # Calculate time taken
        end_time = time.time()
        time_taken = round(end_time - start_time, 2)
        
        # Count successful requests
        successful = sum(1 for r in results if r.get('success', False))
        
        logger.info(f"All concurrent requests completed in {time_taken} seconds ({successful}/5 successful)")
        
        return jsonify({
            'time_taken': time_taken,
            'requests_made': 5,
            'successful_requests': successful,
            'delay_value': delay_value
        }), 200
    
    except Exception as e:
        logger.error(f"Error in concurrent_requests endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/items', methods=['GET'])
def get_items():
    """
    Get all items from database (for testing purposes)
    
    Response:
        200 OK
        Body: [{"id": 1, "item": "book", "status": "pending"}, ...]
    """
    try:
        items = db.get_all_items()
        return jsonify(items), 200
    except Exception as e:
        logger.error(f"Error in get_items endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


@app.route('/')
def index():
    """Serve the main web interface"""
    return send_from_directory('static', 'index.html')


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    return send_from_directory('static', filename)


if __name__ == '__main__':
    logger.info("Starting Flask application...")
    app.run(host='0.0.0.0', port=5000, debug=FLASK_DEBUG)
