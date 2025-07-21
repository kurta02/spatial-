#!/usr/bin/env python3
"""
Test Flask API Wrapper - Verify API endpoints work correctly
"""

import requests
import json
import time
from typing import Dict, Any

def test_api_endpoints(base_url: str = "http://localhost:5001"):
    """Test all API endpoints"""
    
    print("🧪 Flask API Wrapper Test")
    print("=" * 50)
    
    print(f"Testing API at: {base_url}")
    
    # Wait for server to be ready
    print("\n1. Waiting for server...")
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/", timeout=2)
            if response.status_code == 200:
                print("   ✅ Server is ready")
                break
        except requests.exceptions.RequestException:
            if i == max_retries - 1:
                print("   ❌ Server not responding")
                return False
            print(f"   ⏳ Waiting... ({i+1}/{max_retries})")
            time.sleep(1)
    
    # Test results
    tests = []
    
    # Test 1: Health check
    print("\n2. Testing health check...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check: {data.get('status')}")
            print(f"   Memory backend: {data.get('memory_backend', 'unknown')}")
            tests.append(("Health check", True))
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            tests.append(("Health check", False))
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        tests.append(("Health check", False))
    
    # Test 2: System status
    print("\n3. Testing system status...")
    try:
        response = requests.get(f"{base_url}/api/system/status")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                system_data = data.get('data', {})
                print(f"   ✅ System status retrieved")
                print(f"   Session: {system_data.get('session_id', 'unknown')[:20]}...")
                print(f"   Components: {len(system_data.get('components', {}))}")
                tests.append(("System status", True))
            else:
                print(f"   ❌ System status failed: {data.get('error')}")
                tests.append(("System status", False))
        else:
            print(f"   ❌ System status HTTP error: {response.status_code}")
            tests.append(("System status", False))
    except Exception as e:
        print(f"   ❌ System status error: {e}")
        tests.append(("System status", False))
    
    # Test 3: Memory operations
    print("\n4. Testing memory storage...")
    try:
        memory_data = {
            "component": "api_test",
            "entry_type": "test_entry",
            "content": "Testing Flask API memory storage",
            "metadata": {"test": True, "api_version": "1.0"}
        }
        
        response = requests.post(f"{base_url}/api/memory/store", json=memory_data)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                entry_id = data.get('entry_id')
                print(f"   ✅ Memory stored: Entry ID {entry_id}")
                tests.append(("Memory storage", True))
            else:
                print(f"   ❌ Memory storage failed: {data.get('error')}")
                tests.append(("Memory storage", False))
        else:
            print(f"   ❌ Memory storage HTTP error: {response.status_code}")
            tests.append(("Memory storage", False))
    except Exception as e:
        print(f"   ❌ Memory storage error: {e}")
        tests.append(("Memory storage", False))
    
    # Test 4: Memory retrieval
    print("\n5. Testing memory retrieval...")
    try:
        params = {"component": "api_test", "limit": 10}
        response = requests.get(f"{base_url}/api/memory/retrieve", params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                entries = data.get('entries', [])
                count = data.get('count', 0)
                print(f"   ✅ Memory retrieved: {count} entries")
                if entries:
                    print(f"   Latest: {entries[0].get('content', 'N/A')[:50]}...")
                tests.append(("Memory retrieval", True))
            else:
                print(f"   ❌ Memory retrieval failed: {data.get('error')}")
                tests.append(("Memory retrieval", False))
        else:
            print(f"   ❌ Memory retrieval HTTP error: {response.status_code}")
            tests.append(("Memory retrieval", False))
    except Exception as e:
        print(f"   ❌ Memory retrieval error: {e}")
        tests.append(("Memory retrieval", False))
    
    # Test 5: Memory stats
    print("\n6. Testing memory statistics...")
    try:
        response = requests.get(f"{base_url}/api/memory/stats")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                stats = data.get('stats', {})
                print(f"   ✅ Memory stats retrieved")
                print(f"   Total entries: {stats.get('total_entries', 'unknown')}")
                print(f"   Backend: {stats.get('backend', 'unknown')}")
                tests.append(("Memory stats", True))
            else:
                print(f"   ❌ Memory stats failed: {data.get('error')}")
                tests.append(("Memory stats", False))
        else:
            print(f"   ❌ Memory stats HTTP error: {response.status_code}")
            tests.append(("Memory stats", False))
    except Exception as e:
        print(f"   ❌ Memory stats error: {e}")
        tests.append(("Memory stats", False))
    
    # Test 6: Session management
    print("\n7. Testing session management...")
    try:
        response = requests.get(f"{base_url}/api/session/current")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                session_id = data.get('session_id')
                print(f"   ✅ Current session: {session_id[:30]}...")
                tests.append(("Session management", True))
            else:
                print(f"   ❌ Session management failed: {data.get('error')}")
                tests.append(("Session management", False))
        else:
            print(f"   ❌ Session management HTTP error: {response.status_code}")
            tests.append(("Session management", False))
    except Exception as e:
        print(f"   ❌ Session management error: {e}")
        tests.append(("Session management", False))
    
    # Test 7: Error handling
    print("\n8. Testing error handling...")
    try:
        # Test invalid endpoint
        response = requests.get(f"{base_url}/api/invalid/endpoint")
        if response.status_code == 404:
            data = response.json()
            if not data.get('success') and 'not found' in data.get('error', '').lower():
                print("   ✅ 404 error handling works")
                tests.append(("Error handling", True))
            else:
                print(f"   ❌ 404 error format incorrect: {data}")
                tests.append(("Error handling", False))
        else:
            print(f"   ❌ Expected 404, got {response.status_code}")
            tests.append(("Error handling", False))
    except Exception as e:
        print(f"   ❌ Error handling test error: {e}")
        tests.append(("Error handling", False))
    
    # Summary
    print("\n9. Test Summary")
    print("-" * 30)
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    print(f"\nPassed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All API tests passed!")
        return True
    else:
        print("❌ Some API tests failed")
        return False

if __name__ == "__main__":
    import sys
    
    # Default to localhost:5001
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
    
    success = test_api_endpoints(base_url)
    sys.exit(0 if success else 1)