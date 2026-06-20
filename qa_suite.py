import urllib.request
import urllib.error
import json
import time
import subprocess
import sys
import threading
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PORT = 8765
BASE_URL = f"http://127.0.0.1:{PORT}"
SERVER_PROC = None

def start_server():
    global SERVER_PROC
    print("[QA] Starting test server...")
    SERVER_PROC = subprocess.Popen([sys.executable, "server.py"], stdout=subprocess.DEVNULL)
    # Poll until server is up
    for _ in range(10):
        try:
            urllib.request.urlopen(f"{BASE_URL}/", timeout=1)
            print("[QA] Server is up!")
            return
        except Exception as e:
            time.sleep(1)
            
    # If we get here, it failed. Print stderr if any.
    if SERVER_PROC.poll() is not None:
        err = SERVER_PROC.stderr.read() if SERVER_PROC.stderr else b""
        print("[QA] Server exited early. Stderr:", err.decode('utf-8', errors='ignore'))
    print("[QA] Server failed to start or timeout.")

def stop_server():
    global SERVER_PROC
    if SERVER_PROC:
        print("[QA] Stopping test server...")
        SERVER_PROC.terminate()
        SERVER_PROC.wait()

def test_endpoint(url, method="GET", expect_status=200):
    req = urllib.request.Request(url, method=method)
    try:
        response = urllib.request.urlopen(req, timeout=5)
        status = response.getcode()
        body = response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        status = e.code
        body = e.read().decode('utf-8')
    except Exception as e:
        print(f"❌ FAIL: {method} {url} - Connection Error: {e}")
        return False
        
    if status == expect_status:
        print(f"✅ PASS: {method} {url} (Status {status})")
        return True
    else:
        print(f"❌ FAIL: {method} {url} (Expected {expect_status}, got {status})")
        print(f"   Response: {body[:200]}")
        return False

def run_tests():
    print("="*40)
    print(" NarrativeOS QA Automated Suite")
    print("="*40)
    
    start_server()
    
    success = True
    
    # Test 1: Frontend serving
    success &= test_endpoint(f"{BASE_URL}/", expect_status=200)
    success &= test_endpoint(f"{BASE_URL}/static/style.css", expect_status=200)
    
    # Test 2: API Security (Expect 401 Unauthorized since we don't have the dynamic token)
    # The server uses a dynamic APP_TOKEN, so hitting /api/ without it should fail
    success &= test_endpoint(f"{BASE_URL}/api/novels", expect_status=401)
    
    # Test 3: Safe Path security verification
    # Try to hit a static file directly but via path traversal
    success &= test_endpoint(f"{BASE_URL}/api/novels/../../Windows/System32", expect_status=401) # API security blocks first
    
    print("="*40)
    if success:
        print("🎉 ALL QA TESTS PASSED!")
    else:
        print("💥 SOME TESTS FAILED.")
        
    stop_server()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(run_tests())
