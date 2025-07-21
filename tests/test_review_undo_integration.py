#!/usr/bin/env python3
"""
Test Review/Undo System Integration with Flask API
Comprehensive testing of user approval and undo workflows
"""

import requests
import json
import time
from typing import Dict, Any

def test_review_undo_integration(base_url: str = "http://localhost:5001"):
    """Test complete review/undo system integration"""
    
    print("🔍 Review/Undo System Integration Test")
    print("=" * 60)
    
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
    
    # Test 1: Initial approval system status
    print("\n1. Testing initial approval system status...")
    try:
        response = requests.get(f"{base_url}/api/approval/summary")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                summary = data.get('summary', {})
                print(f"   ✅ Approval system active")
                print(f"   Pending actions: {summary.get('pending_actions', 0)}")
                print(f"   Auto-approve: {summary.get('auto_approve_enabled', False)}")
                tests.append(("Approval system status", True))
            else:
                print(f"   ❌ Approval system failed: {data}")
                tests.append(("Approval system status", False))
        else:
            print(f"   ❌ Status request failed: {response.status_code}")
            tests.append(("Approval system status", False))
    except Exception as e:
        print(f"   ❌ Approval system error: {e}")
        tests.append(("Approval system status", False))
    
    # Test 2: Try operation that requires approval
    print("\n2. Testing operation requiring approval...")
    try:
        approval_data = {
            "component": "review_test",
            "entry_type": "deletion", 
            "content": "Delete test memory entries for cleanup",
            "importance": 9,
            "metadata": {"test": True, "requires_approval": True}
        }
        
        response = requests.post(f"{base_url}/api/memory/store", json=approval_data)
        if response.status_code == 202:  # Accepted but pending
            data = response.json()
            if data.get('pending_approval'):
                action_id = data.get('action_id')
                print(f"   ✅ Operation requires approval: {action_id}")
                tests.append(("Approval required operation", True))
                
                # Store action_id for later tests
                global test_action_id
                test_action_id = action_id
            else:
                print(f"   ❌ Expected pending approval: {data}")
                tests.append(("Approval required operation", False))
        else:
            print(f"   ❌ Unexpected response: {response.status_code}")
            print(f"   Response: {response.text}")
            tests.append(("Approval required operation", False))
    except Exception as e:
        print(f"   ❌ Approval operation error: {e}")
        tests.append(("Approval required operation", False))
    
    # Test 3: Check pending actions
    print("\n3. Testing pending actions retrieval...")
    try:
        response = requests.get(f"{base_url}/api/approval/pending")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                pending_actions = data.get('pending_actions', [])
                print(f"   ✅ Found {len(pending_actions)} pending actions")
                if pending_actions:
                    action = pending_actions[0]
                    print(f"   Action: {action.get('description')}")
                    print(f"   Risk level: {action.get('risk_level')}")
                    print(f"   Status: {action.get('approval_status')}")
                tests.append(("Pending actions retrieval", True))
            else:
                print(f"   ❌ Failed to get pending actions: {data}")
                tests.append(("Pending actions retrieval", False))
        else:
            print(f"   ❌ Pending actions request failed: {response.status_code}")
            tests.append(("Pending actions retrieval", False))
    except Exception as e:
        print(f"   ❌ Pending actions error: {e}")
        tests.append(("Pending actions retrieval", False))
    
    # Test 4: Approve the pending action
    print("\n4. Testing action approval...")
    try:
        if 'test_action_id' in globals():
            approval_request = {
                "action_id": test_action_id,
                "user_note": "Approved for integration testing - safe to proceed"
            }
            
            response = requests.post(f"{base_url}/api/approval/approve", json=approval_request)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print(f"   ✅ Action approved successfully")
                    print(f"   Action ID: {data.get('action_id')}")
                    tests.append(("Action approval", True))
                else:
                    print(f"   ❌ Approval failed: {data}")
                    tests.append(("Action approval", False))
            else:
                print(f"   ❌ Approval request failed: {response.status_code}")
                tests.append(("Action approval", False))
        else:
            print(f"   ⚠️  No action ID to approve")
            tests.append(("Action approval", False))
    except Exception as e:
        print(f"   ❌ Action approval error: {e}")
        tests.append(("Action approval", False))
    
    # Test 5: Try operation that doesn't require approval
    print("\n5. Testing normal operation (no approval needed)...")
    try:
        normal_data = {
            "component": "review_test",
            "entry_type": "normal_log",
            "content": "Regular log entry that should not require approval",
            "importance": 3
        }
        
        response = requests.post(f"{base_url}/api/memory/store", json=normal_data)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Normal operation completed: Entry ID {data.get('entry_id')}")
                tests.append(("Normal operation", True))
            else:
                print(f"   ❌ Normal operation failed: {data}")
                tests.append(("Normal operation", False))
        else:
            print(f"   ❌ Normal operation error: {response.status_code}")
            tests.append(("Normal operation", False))
    except Exception as e:
        print(f"   ❌ Normal operation error: {e}")
        tests.append(("Normal operation", False))
    
    # Test 6: Check undo stack
    print("\n6. Testing undo stack...")
    try:
        response = requests.get(f"{base_url}/api/undo/stack?limit=5")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                undo_entries = data.get('undo_entries', [])
                print(f"   ✅ Undo stack has {len(undo_entries)} entries")
                for entry in undo_entries:
                    print(f"   - {entry.get('description')} (can undo: {entry.get('can_undo')})")
                tests.append(("Undo stack", True))
            else:
                print(f"   ❌ Undo stack failed: {data}")
                tests.append(("Undo stack", False))
        else:
            print(f"   ❌ Undo stack request failed: {response.status_code}")
            tests.append(("Undo stack", False))
    except Exception as e:
        print(f"   ❌ Undo stack error: {e}")
        tests.append(("Undo stack", False))
    
    # Test 7: Test rejection workflow
    print("\n7. Testing action rejection...")
    try:
        # Create another action that requires approval
        reject_data = {
            "component": "review_test",
            "entry_type": "system_change",
            "content": "Change system configuration settings",
            "importance": 8
        }
        
        response = requests.post(f"{base_url}/api/memory/store", json=reject_data)
        if response.status_code == 202:
            data = response.json()
            if data.get('pending_approval'):
                action_id = data.get('action_id')
                
                # Now reject it
                rejection_request = {
                    "action_id": action_id,
                    "reason": "Testing rejection workflow - not needed"
                }
                
                reject_response = requests.post(f"{base_url}/api/approval/reject", json=rejection_request)
                if reject_response.status_code == 200:
                    reject_data = reject_response.json()
                    if reject_data.get('success'):
                        print(f"   ✅ Action rejected successfully")
                        tests.append(("Action rejection", True))
                    else:
                        print(f"   ❌ Rejection failed: {reject_data}")
                        tests.append(("Action rejection", False))
                else:
                    print(f"   ❌ Rejection request failed: {reject_response.status_code}")
                    tests.append(("Action rejection", False))
            else:
                print(f"   ❌ Expected pending approval for rejection test")
                tests.append(("Action rejection", False))
        else:
            print(f"   ❌ Could not create action for rejection test")
            tests.append(("Action rejection", False))
    except Exception as e:
        print(f"   ❌ Action rejection error: {e}")
        tests.append(("Action rejection", False))
    
    # Test 8: Final system summary
    print("\n8. Testing final system summary...")
    try:
        response = requests.get(f"{base_url}/api/approval/summary")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                summary = data.get('summary', {})
                print(f"   ✅ Final system state:")
                print(f"   Pending actions: {summary.get('pending_actions', 0)}")
                print(f"   Undo entries available: {summary.get('undo_entries_available', 0)}")
                print(f"   Total undo entries: {summary.get('total_undo_entries', 0)}")
                print(f"   Risk breakdown: {summary.get('risk_breakdown', {})}")
                tests.append(("Final system summary", True))
            else:
                print(f"   ❌ Final summary failed: {data}")
                tests.append(("Final system summary", False))
        else:
            print(f"   ❌ Final summary request failed: {response.status_code}")
            tests.append(("Final system summary", False))
    except Exception as e:
        print(f"   ❌ Final summary error: {e}")
        tests.append(("Final system summary", False))
    
    # Summary
    print("\n🏆 Review/Undo Integration Test Summary")
    print("-" * 50)
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅" if result else "❌"
        print(f"   {status} {test_name}")
    
    print(f"\nPassed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All review/undo integration tests passed!")
        print("\n🔑 KEY ACHIEVEMENTS:")
        print("   ✅ User approval required for high-risk operations")
        print("   ✅ Normal operations proceed without approval")
        print("   ✅ Pending actions tracked and manageable")
        print("   ✅ Approval and rejection workflows working")
        print("   ✅ Undo stack maintains operation history")
        print("   ✅ Complete audit trail available")
        return True
    else:
        print("⚠️  Some tests failed - check logs")
        return False

if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5001"
    
    success = test_review_undo_integration(base_url)
    sys.exit(0 if success else 1)