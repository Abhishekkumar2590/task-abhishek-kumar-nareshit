#!/bin/bash
# Setup and run script for Flask-Celery-RabbitMQ project

echo "================================"
echo "Flask-Celery-RabbitMQ Setup"
echo "================================"

# Check Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

echo "✓ Python found"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -q

echo ""
echo "================================"
echo "Setup Complete!"
echo "================================"
echo ""
echo "Now start in separate terminals:"
echo ""
echo "Terminal 1 (Flask):"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Terminal 2 (Celery Worker):"
echo "  source venv/bin/activate"
echo "  celery -A worker worker --loglevel=info"
echo ""
echo "Terminal 3 (Test):"
echo "  source venv/bin/activate"
echo "  python test_endpoints.py"
echo ""
