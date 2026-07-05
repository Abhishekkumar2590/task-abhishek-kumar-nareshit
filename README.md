# Flask + Celery + RabbitMQ Project

This project demonstrates a distributed task processing system using Flask, Celery, and RabbitMQ with SQLite database and Python threading for concurrent requests.

## Project Overview

### Components:

1. **Producer (Flask API)** - Accepts items and sends them to RabbitMQ
2. **Consumer (Celery Worker)** - Processes messages from RabbitMQ and updates database
3. **Concurrent Requests Endpoint** - Makes multiple concurrent GET requests using threading
4. **Database (SQLite)** - Stores items and their processing status

## Database Schema

```sql
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Table Structure:
- `id`: Auto-incrementing primary key
- `item`: The item name (e.g., "book", "pen")
- `status`: Current status ("pending" or "completed")
- `created_at`: Timestamp when item was created
- `updated_at`: Timestamp when item was last updated

## Prerequisites

Before proceeding, ensure you have:

1. **Python** (3.8 or higher)
2. **RabbitMQ Server** installed and running
3. **pip** (Python package manager)
4. **Git** (optional, for version control)

## Setup Instructions

### Step 1: Install RabbitMQ

**Windows:**
- Download from: https://www.rabbitmq.com/install-windows.html
- Follow the installation wizard
- Ensure RabbitMQ service is running

**macOS:**
```bash
brew install rabbitmq
brew services start rabbitmq
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server
```

### Step 2: Clone or Download the Project

```bash
cd path/to/your/directory
# If using git
git clone <repository-url>
cd flask-celery-project
```

### Step 3: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- **Flask** - Web framework for API endpoints
- **pika** - RabbitMQ Python client
- **celery** - Task queue library
- **requests** - HTTP library for concurrent requests
- **python-dotenv** - Environment variable management

### Step 5: Verify RabbitMQ is Running

```bash
# Test RabbitMQ connection (optional)
# This should work without errors if RabbitMQ is running
python -c "import pika; print('RabbitMQ connection OK')"
```

## Running the Project

### Terminal 1: Start Flask Application (Producer)

```bash
# From the project directory
python app.py
```

You should see:
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

### Terminal 2: Start Celery Worker (Consumer)

```bash
# From the project directory
# Make sure you have activated the virtual environment

celery -A worker worker --loglevel=info
```

You should see:
```
celery@<hostname> v5.3.0 (emerald-rush)
...
[Tasks]
 * worker.process_item
```

### Step 6: Test the API

You can test using:

1. **Postman** (Recommended)
   - Import the `Postman_Collection.json` file
   - Use the provided requests

2. **curl** (Command line)
   ```bash
   # Create an item (Producer)
   curl -X POST http://localhost:5000/api/items \
     -H "Content-Type: application/json" \
     -d '{"item": "book"}'
   
   # Get all items
   curl http://localhost:5000/api/items
   
   # Make concurrent requests
   curl "http://localhost:5000/api/concurrent-requests?delay_value=2"
   ```

3. **Python requests**
   ```python
   import requests
   
   # Create item
   response = requests.post('http://localhost:5000/api/items', 
                           json={'item': 'book'})
   print(response.status_code)  # Should print 202
   
   # Get all items
   response = requests.get('http://localhost:5000/api/items')
   print(response.json())
   ```

## API Endpoints

### 1. Create Item (Producer)

**Endpoint:** `POST /api/items`

**Request:**
```json
{
  "item": "book"
}
```

**Response:** `202 Accepted`

**Description:** Inserts item to database with status='pending' and sends to RabbitMQ

---

### 2. Get All Items

**Endpoint:** `GET /api/items`

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "item": "book",
    "status": "pending"
  },
  {
    "id": 2,
    "item": "pen",
    "status": "completed"
  }
]
```

**Description:** Retrieves all items from database

---

### 3. Concurrent Requests

**Endpoint:** `GET /api/concurrent-requests?delay_value=2`

**Query Parameters:**
- `delay_value` (required): Integer representing seconds of delay

**Response:** `200 OK`
```json
{
  "time_taken": 2.35,
  "requests_made": 5,
  "successful_requests": 5,
  "delay_value": 2
}
```

**Description:** Makes 5 concurrent GET requests to httpbin.org/delay/{delay_value} using threading and returns total execution time

---

### 4. Health Check

**Endpoint:** `GET /api/health`

**Response:** `200 OK`
```json
{
  "status": "healthy"
}
```

## Project Workflow

1. **Producer (API)** receives a POST request with `{"item": "book"}`
2. **Producer** inserts the item into SQLite with `status='pending'`
3. **Producer** sends the item to RabbitMQ queue
4. **Consumer (Celery Worker)** receives the message from RabbitMQ
5. **Consumer** processes the message and updates the database status to `'completed'`
6. Database now shows the item with `status='completed'`

## Key Features

### 1. Raw JSON Payload Handling
- The Celery worker accepts raw JSON payloads without Flask-Celery bindings
- This makes it compatible with producers from other frameworks (Node.js, Go, etc.)

### 2. Duplicate Item Handling
- When updating item status, the worker only updates a single row
- It finds the first pending item with that name and updates only that row
- This prevents accidental bulk updates

### 3. Concurrent Threading
- Uses `ThreadPoolExecutor` to make 5 concurrent requests
- All 5 requests run simultaneously
- Total time is approximately the time of 1 request (not 5x)
- Perfect for measuring concurrency benefits

### 4. Configuration Management
- All settings are centralized in `config.py`
- Environment variables can override default values
- Easy to change queue names, exchange names, database paths

## File Structure

```
flask-celery-project/
├── app.py                      # Flask application with endpoints
├── worker.py                   # Celery worker for consuming messages
├── database.py                 # Database manager and models
├── config.py                   # Configuration settings
├── requirements.txt            # Python dependencies
├── Postman_Collection.json     # Postman collection for testing
├── README.md                   # This file
└── tasks.db                    # SQLite database (created on first run)
```

## Troubleshooting

### Issue: "Connection refused" when connecting to RabbitMQ

**Solution:**
- Verify RabbitMQ is running: `rabbitmqctl status`
- On Windows: Check Services (search for "Services" in Windows)
- Restart RabbitMQ service if needed

### Issue: "ModuleNotFoundError" when running app

**Solution:**
- Verify virtual environment is activated
- Reinstall requirements: `pip install -r requirements.txt`

### Issue: "Database is locked"

**Solution:**
- This typically happens with concurrent access
- The code uses proper connection handling
- Close any other database connections (Excel, DB viewers)

### Issue: Celery worker not consuming messages

**Solution:**
- Verify RabbitMQ is running
- Check celery worker terminal for error messages
- Verify worker is listening to correct queue: Check logs for "Queue: item_queue"

### Issue: Messages not being processed

**Solution:**
- Check that both Flask app and Celery worker are running
- Look at Celery worker logs for errors
- Verify database file has write permissions

## Configuration Customization

To change settings, edit `config.py`:

```python
# RabbitMQ settings
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'

# Queue settings
QUEUE_NAME = 'item_queue'
EXCHANGE_NAME = 'item_exchange'
ROUTING_KEY = 'item_task'

# Database
DATABASE_FILE = 'tasks.db'
```

Or use environment variables:

```bash
export RABBITMQ_HOST=your-host
export QUEUE_NAME=custom_queue
python app.py
```

## Testing Workflow

### Test 1: Basic Producer-Consumer

1. Start Flask app
2. Start Celery worker
3. Send POST request: `{"item": "book"}`
4. Check database - item should have status='pending' initially
5. Wait a moment for Celery to process
6. Check database again - status should be='completed'

### Test 2: Multiple Items

1. Send multiple POST requests with different items: book, pen, notebook
2. Check GET /api/items
3. Verify all items show in database
4. When Celery worker processes, status should update to completed

### Test 3: Concurrent Requests

1. Send GET request with `delay_value=1`
2. Verify response shows time_taken is approximately 1-2 seconds (not 5+ seconds)
3. Try with different delay_values: 2, 3, 5
4. Time should remain roughly the same (the delay value), not multiply by 5

## Performance Notes

- **Concurrent Threading**: With 5 concurrent requests to a service with 2-second delay, total time ≈ 2 seconds (not 10 seconds)
- **Database**: SQLite is suitable for development; for production, consider PostgreSQL
- **Worker Scaling**: Can run multiple Celery workers for higher throughput
- **Message Persistence**: Messages are marked as durable in RabbitMQ config

## Next Steps / Advanced Topics

1. **Add More Endpoints**: Expand with additional processing logic
2. **Error Handling**: Implement retry logic and dead-letter queues
3. **Monitoring**: Add health checks and metrics
4. **Scaling**: Deploy with Docker and Kubernetes
5. **Testing**: Add unit tests and integration tests
6. **Database**: Migrate to PostgreSQL for production
7. **Authentication**: Add API key validation

## Architectural Questions to Prepare

Before the next round of discussions, be prepared to answer questions about:

1. **RabbitMQ**: Queue vs Topic exchange, message persistence, acknowledgments
2. **Celery**: Task routing, retries, timeouts, task states
3. **Flask**: Request/response cycle, blueprints, error handling
4. **Threading**: GIL, locks, concurrent.futures, threading vs asyncio
5. **SQLite**: ACID properties, transactions, limitations at scale
6. **Design Patterns**: Producer-consumer, asynchronous processing, microservices

## License

This project is provided for educational purposes.

## Support

For issues or questions, refer to the official documentation:
- Flask: https://flask.palletsprojects.com/
- Celery: https://docs.celeryproject.io/
- RabbitMQ: https://www.rabbitmq.com/documentation.html
- Python Requests: https://docs.python-requests.org/
# task-abhishek-kumar-
# task-abhishek-kumar-nareshit
