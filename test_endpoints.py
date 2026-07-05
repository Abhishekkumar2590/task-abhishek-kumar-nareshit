"""
Quick test script to verify the application setup
Run this after starting Flask app and Celery worker
"""
import requests
import json
import time
import sys

BASE_URL = 'http://localhost:5000'

def test_health():
    """Test health endpoint"""
    print("\n=== Testing Health Endpoint ===")
    try:
        response = requests.get(f'{BASE_URL}/api/health')
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_create_item(item_name):
    """Test creating an item"""
    print(f"\n=== Creating Item: {item_name} ===")
    try:
        payload = {'item': item_name}
        response = requests.post(
            f'{BASE_URL}/api/items',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text if response.text else 'No body (expected for 202)'}")
        return response.status_code == 202
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_get_items():
    """Test getting all items"""
    print("\n=== Getting All Items ===")
    try:
        response = requests.get(f'{BASE_URL}/api/items')
        print(f"Status: {response.status_code}")
        items = response.json()
        print(f"Items found: {len(items)}")
        if items:
            print("Items:")
            for item in items:
                print(f"  - ID: {item['id']}, Item: {item['item']}, Status: {item['status']}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_concurrent_requests(delay_value=1):
    """Test concurrent requests"""
    print(f"\n=== Testing Concurrent Requests (delay={delay_value}) ===")
    try:
        response = requests.get(
            f'{BASE_URL}/api/concurrent-requests',
            params={'delay_value': delay_value}
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Time taken: {data['time_taken']} seconds")
        print(f"Requests made: {data['requests_made']}")
        print(f"Successful requests: {data['successful_requests']}")
        print(f"Note: With {delay_value} second delay and 5 concurrent requests,")
        print(f"      total time should be ~{delay_value}-{delay_value+1} seconds (not {delay_value*5})")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    print("=" * 50)
    print("Flask-Celery-RabbitMQ Application Test Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        requests.get(f'{BASE_URL}/api/health', timeout=2)
    except requests.exceptions.ConnectionError:
        print("\nERROR: Cannot connect to Flask application!")
        print("Please ensure Flask app is running: python app.py")
        sys.exit(1)
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health()))
    results.append(("Create Item - book", test_create_item("book")))
    
    # Wait for Celery to process
    print("\n>>> Waiting 3 seconds for Celery worker to process message...")
    time.sleep(3)
    
    results.append(("Get Items", test_get_items()))
    results.append(("Create Item - pen", test_create_item("pen")))
    
    time.sleep(2)
    
    results.append(("Concurrent Requests (delay=1)", test_concurrent_requests(1)))
    
    # Print summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All tests passed! Application is working correctly.")
    else:
        print(f"\n✗ {total - passed} test(s) failed. Check Flask and Celery worker logs.")
    
    return 0 if passed == total else 1

if __name__ == '__main__':
    sys.exit(main())
