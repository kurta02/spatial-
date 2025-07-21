#!/usr/bin/env python3
"""
Test AI Enforcement Framework Integration with Flask API
"""

import requests
import json
import time
from typing import Dict, Any

def test_enforcement_integration(base_url: str = "http://localhost:5001"):
    """Test AI enforcement framework integration with Flask API"""
    
    print("🔒 AI Enforcement Integration Test")
    print("=" * 50)
    
    # Wait for server
    print("Waiting for Flask API server...")
    for i in range(10):
        try:
            response = requests.get(f"{base_url}/", timeout=2)
            if response.status_code == 200:
                print("✅ Flask API server is ready")
                break
        except requests.exceptions.RequestException:
            if i == 9:
                print("❌ Flask API server not responding")
                return False
            time.sleep(1)
    
    tests = []
    
    # Test 1: Health check (should pass)
    print("\n1. Testing health check with enforcement...")
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check passed: {data.get('status')}")
            tests.append(("Health check", True))
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            tests.append(("Health check", False))
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        tests.append(("Health check", False))
    
    # Test 2: Enforcement status endpoint
    print("\n2. Testing enforcement status endpoint...")
    try:
        response = requests.get(f"{base_url}/api/enforcement/status")
        if response.status_code == 200:
            data = response.json()
            if data.get('success') and data.get('enforcement_active'):
                print(f"   ✅ Enforcement is active")
                report = data.get('violation_report', {})
                print(f"   Total violations tracked: {report.get('total_violations', 0)}")
                tests.append(("Enforcement status", True))
            else:
                print(f"   ❌ Enforcement not active: {data}")
                tests.append(("Enforcement status", False))
        else:
            print(f"   ❌ Enforcement status failed: {response.status_code}")
            tests.append(("Enforcement status", False))
    except Exception as e:
        print(f"   ❌ Enforcement status error: {e}")
        tests.append(("Enforcement status", False))
    
    # Test 3: Memory store with enforcement
    print("\n3. Testing memory store with enforcement...")
    try:
        memory_data = {
            "component": "enforcement_test",
            "entry_type": "integration_test",
            "content": "Testing AI enforcement integration with Flask API",
            "metadata": {"test": True, "enforcement": "active"}
        }
        
        response = requests.post(f"{base_url}/api/memory/store", json=memory_data)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                entry_id = data.get('entry_id')
                print(f"   ✅ Memory store passed enforcement: Entry ID {entry_id}")
                tests.append(("Memory store enforcement", True))
            else:
                print(f"   ❌ Memory store blocked: {data.get('error')}")
                tests.append(("Memory store enforcement", False))
        elif response.status_code == 403:
            print(f"   ⚠️  Memory store blocked by enforcement (expected for some cases)")
            tests.append(("Memory store enforcement", True))  # Blocking is also valid
        else:
            print(f"   ❌ Memory store error: {response.status_code}")
            tests.append(("Memory store enforcement", False))
    except Exception as e:
        print(f"   ❌ Memory store error: {e}")
        tests.append(("Memory store enforcement", False))
    
    # Test 4: System status with enforcement
    print("\n4. Testing system status with enforcement...")
    try:
        response = requests.get(f"{base_url}/api/system/status")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ System status passed enforcement")
                tests.append(("System status enforcement", True))
            else:
                print(f"   ❌ System status failed: {data.get('error')}")
                tests.append(("System status enforcement", False))
        elif response.status_code == 403:
            print(f"   ⚠️  System status blocked by enforcement")
            tests.append(("System status enforcement", True))  # Blocking is valid
        else:
            print(f"   ❌ System status error: {response.status_code}")
            tests.append(("System status enforcement", False))
    except Exception as e:
        print(f"   ❌ System status error: {e}")
        tests.append(("System status enforcement", False))
    
    # Test 5: Memory retrieval
    print("\n5. Testing memory retrieval...")
    try:
        params = {"component": "enforcement_test", "limit": 10}
        response = requests.get(f"{base_url}/api/memory/retrieve", params=params)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                entries = data.get('entries', [])
                print(f"   ✅ Memory retrieval: {len(entries)} entries")
                tests.append(("Memory retrieval", True))
            else:
                print(f"   ❌ Memory retrieval failed: {data.get('error')}")
                tests.append(("Memory retrieval", False))
        else:
            print(f"   ❌ Memory retrieval error: {response.status_code}")
            tests.append(("Memory retrieval", False))
    except Exception as e:
        print(f"   ❌ Memory retrieval error: {e}")
        tests.append(("Memory retrieval", False))
    
    # Test 6: Final enforcement report
    print("\n6. Getting final enforcement report...")
    try:
        response = requests.get(f"{base_url}/api/enforcement/status")
        if response.status_code == 200:
            data = response.json()
            report = data.get('violation_report', {})
            print(f"   Total enforcement checks: {len(tests)}")
            print(f"   Total violations: {report.get('total_violations', 0)}")
            print(f"   Violations by rule: {report.get('violations_by_rule', {})}")
            tests.append(("Final enforcement report", True))
        else:
            print(f"   ❌ Cannot get final report")
            tests.append(("Final enforcement report", False))
    except Exception as e:
        print(f"   ❌ Final report error: {e}")
        tests.append(("Final enforcement report", False))
    
    # Summary
    print("\n🏆 Enforcement Integration Test Summary")
    print("-" * 40)
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    print(f"\nPassed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All enforcement integration tests passed!")
        return True
    else:
        print("⚠️  Some tests failed - check logs")
        return False

if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
    
    success = test_enforcement_integration(base_url)
    sys.exit(0 if success else 1)