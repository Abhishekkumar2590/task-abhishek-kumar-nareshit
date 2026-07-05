# Architecture and Technical Documentation

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FLASK API (Producer)                         │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  POST /api/items                                              │  │
│  │  - Accepts: {"item": "book"}                                  │  │
│  │  - Inserts into SQLite with status='pending'                  │  │
│  │  - Sends message to RabbitMQ                                  │  │
│  │  - Returns: HTTP 202 (Accepted)                               │  │
│  └───────────────────────────────────────────────────────────────┘  │
└────────┬──────────────────────────────────────────────────────┬─────┘
         │                                                      │
         │                                            GET /api/concurrent-requests
         │                                            ┌─────────────────────────────┐
         │                                            │  Makes 5 concurrent requests│
         │                                            │  to httpbin.org/delay/{val}│
         │                                            │  Using ThreadPoolExecutor   │
         │                                            │  Returns: time_taken (JSON)│
         │                                            └─────────────────────────────┘
         ▼
    ┌─────────────┐
    │  RabbitMQ   │                          ┌──────────────────────┐
    │             │◄─────── Queue ─────────►│ Message: {"item":"book"} │
    │  Exchange   │      (item_queue)      └──────────────────────┘
    │             │
    └─────────────┘
         ▲
         │
         │ Consumes message
         │
    ┌─────────────────────────────────────────────────────────────┐
    │       CELERY WORKER (Consumer)                              │
    │  ┌─────────────────────────────────────────────────────┐   │
    │  │  process_item(payload)                              │   │
    │  │  - Receives: {"item": "book"} (raw JSON)            │   │
    │  │  - Updates SQLite: status='pending' → 'completed'   │   │
    │  │  - Handles duplicate items carefully (single row)   │   │
    │  │  - Logs success/error                               │   │
    │  └─────────────────────────────────────────────────────┘   │
    └────────┬─────────────────────────────────────────────────┘
             │
             ▼
         ┌────────────────────┐
         │   SQLite Database  │
         │   (tasks.db)       │
         │                    │
         │  items table:      │
         │  id, item, status  │
         └────────────────────┘
```

## Component Details

### 1. Flask Application (Producer)
**File:** `app.py`

**Responsibilities:**
- Listen for POST requests on `/api/items`
- Validate incoming JSON payload
- Insert items into SQLite database with `status='pending'`
- Publish messages to RabbitMQ
- Return HTTP 202 (Accepted) to client
- Provide concurrent request endpoint for testing

**Key Functions:**
- `send_to_rabbitmq()`: Handles RabbitMQ connection and message publishing
- `create_item()`: POST endpoint for producer
- `concurrent_requests()`: GET endpoint for concurrent threading
- `get_items()`: GET endpoint to view all items

**Communication:**
- Outbound: Sends messages to RabbitMQ
- Database: Writes to SQLite

---

### 2. Celery Worker (Consumer)
**File:** `worker.py`

**Responsibilities:**
- Connect to RabbitMQ broker
- Listen to the queue for messages
- Process incoming messages asynchronously
- Update database when processing completes
- Handle errors gracefully

**Key Functions:**
- `process_item()`: Celery task that processes items
- Receives raw JSON payload from RabbitMQ
- Updates only a single row (even if item names duplicate)
- Logs all operations

**Communication:**
- Inbound: Receives messages from RabbitMQ
- Database: Reads/updates SQLite

**Design Decision:** Works with raw JSON payloads without Flask-Celery bindings
- Allows producer from any framework (Node.js, Go, Python, etc.)
- Only requires JSON payload format
- Makes system loosely coupled

---

### 3. Database
**File:** `database.py`

**Schema:**
```
items table:
- id: INTEGER PRIMARY KEY AUTOINCREMENT
- item: VARCHAR(20) NOT NULL
- status: VARCHAR(20) NOT NULL DEFAULT 'pending'
- created_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
- updated_at: TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

**Key Methods:**
- `insert_item(item)`: Insert new item with status='pending'
- `update_item_status(item, status)`: Update status for first pending item with that name
- `get_all_items()`: Retrieve all items
- `get_item_by_id(item_id)`: Retrieve specific item

**Duplicate Item Handling:**
When multiple items have the same name, the worker:
1. Queries for the FIRST pending item with that name
2. Orders by created_at (FIFO)
3. Updates ONLY that one row
4. Prevents accidental bulk updates

---

### 4. Configuration
**File:** `config.py`

**Contains:**
- Flask settings (debug, environment)
- Database configuration (SQLite file path)
- RabbitMQ connection details (host, port, credentials)
- Queue/Exchange configuration (names, routing keys)
- Celery configuration (broker, backend)

**Features:**
- Uses environment variables for overrides
- Default values for development
- Easy to customize for different environments

---

## Message Flow

### Producer-Consumer Workflow

```
1. Client sends POST request
   POST /api/items
   {"item": "book"}
        │
        ▼
2. Flask validates and processes
   - Checks JSON format
   - Validates 'item' parameter
   - Prepares database insert
        │
        ▼
3. Database insert
   INSERT INTO items (item, status)
   VALUES ('book', 'pending')
   ✓ Database now has: id=1, item='book', status='pending'
        │
        ▼
4. Send to RabbitMQ
   - Create connection to RabbitMQ
   - Declare exchange (durable, direct)
   - Declare queue (durable)
   - Bind queue to exchange
   - Publish message as JSON
   ✓ Message in queue: {"item": "book"}
        │
        ▼
5. Return 202 to client
   HTTP 202 Accepted
        │
        ▼
6. Celery worker receives message
   - Connects to RabbitMQ
   - Monitors queue for messages
   - Receives: {"item": "book"}
        │
        ▼
7. Process message
   - Parse JSON
   - Extract 'item' field
   - Find first pending item in database
   - Validate found
        │
        ▼
8. Update database
   UPDATE items
   SET status = 'completed'
   WHERE id = 1 (first pending 'book')
   ✓ Database now: id=1, item='book', status='completed'
        │
        ▼
9. Acknowledge message
   - Send ACK to RabbitMQ
   - Message removed from queue
```

## Concurrent Threading Flow

```
GET /api/concurrent-requests?delay_value=2
        │
        ▼
Validate delay_value parameter
        │
        ▼
Start timer: start_time = time.time()
        │
        ▼
Create ThreadPoolExecutor with 5 workers
        │
        ├─ Thread 1: GET https://httpbin.org/delay/2
        ├─ Thread 2: GET https://httpbin.org/delay/2
        ├─ Thread 3: GET https://httpbin.org/delay/2
        ├─ Thread 4: GET https://httpbin.org/delay/2
        └─ Thread 5: GET https://httpbin.org/delay/2
        │
        │ All threads run CONCURRENTLY
        │ (not sequentially)
        │
        ▼
Wait for all threads to complete
        │
        ▼
End timer: end_time = time.time()
time_taken = end_time - start_time
        │
        ▼
Return response
{
  "time_taken": 2.35,
  "requests_made": 5,
  "successful_requests": 5,
  "delay_value": 2
}
```

**Why ~2.35 seconds and not ~10 seconds?**
- 5 requests each taking 2 seconds = 10 seconds sequentially
- But they run CONCURRENTLY (parallel)
- So total time ≈ time for 1 request + overhead
- Result: ~2-2.5 seconds instead of ~10 seconds

---

## RabbitMQ Queue Configuration

### Queue Setup

```python
# Exchange Declaration
type: direct
durable: True
auto_delete: False

# Queue Declaration
name: item_queue
durable: True
auto_delete: False

# Binding
routing_key: item_task

# Message Properties
delivery_mode: 2 (persistent)
content_type: application/json
```

### Message Format

```json
{
  "item": "book"
}
```

Celery automatically wraps this in a task envelope, but the worker can extract the raw payload.

---

## Celery Configuration

### Task Definition

```python
@app.task(name='process_item', bind=True)
def process_item(self, payload):
    # self: reference to the task instance
    # payload: the message from RabbitMQ
```

### Routing

```python
app.conf.task_default_exchange = 'item_exchange'
app.conf.task_default_routing_key = 'item_task'
```

### Result Backend

```python
result_backend: 'db+sqlite:///celery_results.db'
```

Stores task state/results (optional, not critical for this workflow)

---

## Error Handling

### Producer (Flask)

```python
try:
    # Validate input
    if not request.is_json:
        return error 400
    
    # Validate data
    if 'item' not in data:
        return error 400
    
    # Insert to DB
    item_id = db.insert_item(item)
    
    # Send to RabbitMQ
    if send_to_rabbitmq(payload):
        return 202
    else:
        # Still return 202 (item saved to DB)
        # RabbitMQ retry possible later
        return 202

except Exception as e:
    log error
    return 500
```

### Consumer (Celery)

```python
@app.task(bind=True)
def process_item(self, payload):
    try:
        # Parse payload
        if isinstance(payload, str):
            data = json.loads(payload)
        else:
            data = payload
        
        # Validate
        item = data.get('item')
        if not item:
            return error response
        
        # Update database
        success = db.update_item_status(item, 'completed')
        
        if success:
            return success response
        else:
            return no_item_found response
    
    except Exception as e:
        log error
        return error response
```

---

## Database Transactions

### SQLite Transaction Management

```python
with self.get_connection() as conn:
    cursor = conn.cursor()
    
    # Execute query
    cursor.execute(sql, params)
    
    # Auto-commit on context manager exit
    conn.commit()
```

**Features:**
- ACID compliance (SQLite supports transactions)
- Auto-rollback on exception
- Thread-safe connection per request
- Serializable isolation level (default for SQLite)

---

## Threading in Concurrent Requests

### ThreadPoolExecutor Pattern

```python
with ThreadPoolExecutor(max_workers=5) as executor:
    # Submit 5 tasks
    futures = [
        executor.submit(make_request, url, i+1)
        for i in range(5)
    ]
    
    # Wait for completion and collect results
    for future in as_completed(futures):
        result = future.result()
        results.append(result)
```

**Advantages:**
- Simpler than manual thread creation
- Automatic resource management
- Built-in exception handling
- as_completed() returns in completion order

**Note on GIL:**
- Python's Global Interpreter Lock prevents true parallelism
- But threading still helps with I/O-bound operations
- Network requests release the GIL
- So concurrent I/O operations are actually parallel

---

## Performance Considerations

### 1. Database
- SQLite is single-writer (acceptable for this scale)
- Each connection creates a new connection object
- Good for < 1,000 req/sec

### 2. RabbitMQ
- Durable messages survive broker restart
- Connection pooling recommended for production
- Each producer creates a new connection (acceptable for this demo)

### 3. Celery
- Single worker processes tasks sequentially by default
- Can scale horizontally with multiple workers
- Task processing time depends on database update speed

### 4. Threading
- 5 concurrent requests to external service
- Timeout: 60 seconds per request
- Network I/O bound, so threading is efficient

---

## Scalability Path

### Current State
```
Single Flask instance → RabbitMQ ← Single Celery worker
```

### Scaled State
```
Load Balancer
├─ Flask instance 1 ──┐
├─ Flask instance 2   ├──► RabbitMQ ◄─── Celery worker 1
├─ Flask instance N ──┘                    Celery worker 2
                                           Celery worker N
                                           
Database: PostgreSQL (replace SQLite)
```

---

## Testing Scenarios

### Scenario 1: Single Item
1. Send POST with item="book"
2. Check GET /api/items
3. Verify status=pending
4. Wait for worker
5. Verify status=completed

### Scenario 2: Duplicate Items
1. Send POST with item="book" → ID=1
2. Send POST with item="book" → ID=2
3. Send POST with item="book" → ID=3
4. Worker processes: only ID=1 updated (first pending)
5. Send POST again with item="book" → ID=4
6. Worker processes: only ID=2 updated (next first pending)

### Scenario 3: Concurrent Performance
1. Send GET with delay_value=2
2. Measure time: should be ~2 seconds (not 10)
3. Verify all 5 requests succeeded
4. Prove concurrency benefit

### Scenario 4: Error Cases
1. Send POST without "item" field → 400
2. Send POST with wrong content-type → 400
3. Stop RabbitMQ → Producer still works (item saved to DB)
4. Send GET with invalid delay_value → 400

---

## Pre-Round Preparation Topics

### RabbitMQ Deep Dive
- [ ] Exchange types: Direct, Topic, Fanout, Headers
- [ ] Queue properties: Durable, Exclusive, Auto-delete
- [ ] Message persistence and TTL
- [ ] Acknowledgment modes: Auto, Manual
- [ ] Dead Letter Exchanges (DLX)

### Celery Deep Dive
- [ ] Task states: Pending, Started, Success, Failure, Retry
- [ ] Task routing and priority queues
- [ ] Retry mechanisms and exponential backoff
- [ ] Task timeouts and soft/hard limits
- [ ] Result backends and result expiry

### Flask Deep Dive
- [ ] Request/response cycle and context
- [ ] Error handling and status codes
- [ ] Decorators: @app.route, @app.before_request, @app.after_request
- [ ] Blueprints for modular applications
- [ ] Application factory pattern

### Threading Deep Dive
- [ ] Global Interpreter Lock (GIL)
- [ ] I/O-bound vs CPU-bound operations
- [ ] Thread safety and race conditions
- [ ] Locks, semaphores, conditions
- [ ] ThreadPoolExecutor vs asyncio

### SQLite Deep Dive
- [ ] ACID properties
- [ ] Transactions and isolation levels
- [ ] Indexes and query optimization
- [ ] Limitations: concurrent writes, max file size
- [ ] Migration to PostgreSQL

---

## References

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Celery Documentation](https://docs.celeryproject.io/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)
- [Python Threading](https://docs.python.org/3/library/threading.html)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Pika Documentation](https://pika.readthedocs.io/)
