# QUICKSTART GUIDE

## 5-Minute Setup & Run

### Prerequisites Checklist
- [ ] Python 3.8+ installed
- [ ] RabbitMQ server installed
- [ ] Git installed (optional)

### Step 1: Start RabbitMQ (1 minute)

**Windows:**
1. Search for "Services" in Windows
2. Find "RabbitMQ" service
3. Right-click → "Start"
4. Or if installed, run: `rabbitmq-server.bat`

**macOS:**
```bash
brew services start rabbitmq
```

**Linux:**
```bash
sudo systemctl start rabbitmq-server
```

**Verify:**
```bash
rabbitmqctl status
```

---

### Step 2: Install Python Dependencies (2 minutes)

```bash
# Navigate to project directory
cd flask-celery-project

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 3: Run Flask App (Terminal 1)

```bash
python app.py
```

**Expected Output:**
```
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

---

### Step 4: Run Celery Worker (Terminal 2)

```bash
# Make sure virtual environment is activated
celery -A worker worker --loglevel=info
```

**Expected Output:**
```
celery@hostname v5.3.0
...
[Tasks]
 * worker.process_item
```

---

### Step 5: Test the Application (Terminal 3)

```bash
# Navigate to project directory
cd flask-celery-project

# Activate virtual environment
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# Run test script
python test_endpoints.py
```

---

## Manual Testing with Postman

1. **Open Postman**
2. **Import Collection:**
   - File → Import
   - Select `Postman_Collection.json`

3. **Run Requests in Order:**
   - POST /api/items (Create book)
   - Wait 3 seconds
   - GET /api/items (Check status changed to completed)
   - GET /api/concurrent-requests?delay_value=2
   - Verify time_taken is ~2 seconds

---

## Manual Testing with curl

```bash
# Create an item
curl -X POST http://localhost:5000/api/items \
  -H "Content-Type: application/json" \
  -d '{"item": "book"}'

# Response: 202 (no body)

# Check items (before Celery processes)
curl http://localhost:5000/api/items

# Response: [{"id": 1, "item": "book", "status": "pending"}]

# Wait 2 seconds

# Check again (Celery should have processed)
curl http://localhost:5000/api/items

# Response: [{"id": 1, "item": "book", "status": "completed"}]

# Test concurrent requests
curl "http://localhost:5000/api/concurrent-requests?delay_value=2"

# Response: {"time_taken": 2.35, "requests_made": 5, ...}
```

---

## Troubleshooting

### Problem: "Connection refused" for RabbitMQ

**Solution:**
```bash
# Check if RabbitMQ is running
rabbitmqctl status

# If not running, start it
# Windows: Run rabbitmq-server.bat
# macOS: brew services start rabbitmq
# Linux: sudo systemctl start rabbitmq-server
```

### Problem: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
# Verify virtual environment is activated (you should see (venv) in terminal)
# Then reinstall:
pip install -r requirements.txt
```

### Problem: Celery worker not consuming messages

**Solution:**
1. Verify RabbitMQ is running
2. Check if worker shows: `[Tasks] * worker.process_item`
3. Look for errors in worker terminal
4. Restart both Flask and Worker

### Problem: "Database is locked"

**Solution:**
- Close any other database viewers (Excel, DB Browser)
- Ensure only Flask and Celery worker are accessing the database
- Delete `tasks.db` and restart (will recreate on first run)

---

## Quick Command Reference

| Task | Command |
|------|---------|
| Activate venv (Windows) | `venv\Scripts\activate` |
| Activate venv (macOS/Linux) | `source venv/bin/activate` |
| Install dependencies | `pip install -r requirements.txt` |
| Start Flask app | `python app.py` |
| Start Celery worker | `celery -A worker worker --loglevel=info` |
| Run tests | `python test_endpoints.py` |
| Check RabbitMQ status | `rabbitmqctl status` |
| View all items | `curl http://localhost:5000/api/items` |
| Create item | `curl -X POST http://localhost:5000/api/items -H "Content-Type: application/json" -d '{"item":"book"}'` |
| Concurrent requests | `curl "http://localhost:5000/api/concurrent-requests?delay_value=2"` |

---

## Verify Everything Works

✓ Flask app running on port 5000
✓ Celery worker connected to RabbitMQ
✓ RabbitMQ server running
✓ Database file created (tasks.db)
✓ All endpoints responding correctly

### Check Points:

1. **Health Check:**
   ```bash
   curl http://localhost:5000/api/health
   # Response: {"status": "healthy"}
   ```

2. **Create Item:**
   ```bash
   curl -X POST http://localhost:5000/api/items \
     -H "Content-Type: application/json" \
     -d '{"item":"pen"}'
   # Response: 202
   ```

3. **Verify Processing:**
   ```bash
   curl http://localhost:5000/api/items
   # Response should show item with status changed
   ```

4. **Concurrent Requests:**
   ```bash
   curl "http://localhost:5000/api/concurrent-requests?delay_value=1"
   # Response: {"time_taken": ~1.X, ...}
   ```

---

## File Descriptions

| File | Purpose |
|------|---------|
| `app.py` | Flask application with API endpoints |
| `worker.py` | Celery worker for processing tasks |
| `database.py` | SQLite database manager |
| `config.py` | Configuration settings |
| `requirements.txt` | Python dependencies |
| `README.md` | Comprehensive documentation |
| `ARCHITECTURE.md` | Technical architecture details |
| `Postman_Collection.json` | Postman test collection |
| `test_endpoints.py` | Automated test script |
| `.gitignore` | Git ignore rules |

---

## Next Steps

1. **Familiarize with architecture** - Read ARCHITECTURE.md
2. **Explore the code** - Understand each file's purpose
3. **Study RabbitMQ basics** - Queue vs Exchange, routing
4. **Study Celery patterns** - Task routing, states, retries
5. **Prepare for technical questions** - See ARCHITECTURE.md for topics

---

## Need Help?

1. Check **README.md** for detailed documentation
2. Check **ARCHITECTURE.md** for technical details
3. Review **test_endpoints.py** to understand expected behavior
4. Check official docs:
   - Flask: https://flask.palletsprojects.com/
   - Celery: https://docs.celeryproject.io/
   - RabbitMQ: https://www.rabbitmq.com/documentation.html

---

**You're ready to go! Follow the 5 steps above and you should have everything running in ~5 minutes.**
