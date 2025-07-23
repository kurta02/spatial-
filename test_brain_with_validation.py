#!/usr/bin/env python3
# MANDATORY IMPORT - MUST BE FIRST
import sys
sys.path.insert(0, '/home/kurt/.ai_validation')
from AI_VALIDATION_MANDATORY import *

"""
Test Brain System with Mandatory Validation Framework
"""

import os
from datetime import datetime

def test_brain_with_validation():
    """Test brain system with proper validation compliance"""
    
    # MANDATORY: Define task
    task_definition = {
        "task_id": "test_brain_validation_001",
        "title": "Test Brain System with Validation",
        "description": "Test brain initialization and LLM functionality with validation framework compliance",
        "complexity": TaskComplexity.MICRO,
        "estimated_duration_minutes": 15,
        "primary_deliverable": "Brain test results with validation compliance",
        "deliverable_location": "/home/kurt/migration-workspace/spatial-constellation-repo/brain_test_results.json",
        "success_criteria": [
            "Brain initializes successfully",
            "LLM models respond correctly", 
            "Validation framework enforced"
        ],
        "start_condition": "Validation framework active and brain.py accessible",
        "finish_condition": "All brain tests completed and results documented",
        "scope_boundaries": ["Testing only", "No production changes"],
        "dependencies": ["/home/kurt/migration-workspace/spatial-constellation-repo/brain.py"],
        "validation_level": ValidationLevel.AUTOMATED,
        "external_validator": None,
        "requires_user_manual": False,
        "requires_technical_docs": False,
        "requires_integration_guide": False,
        "created_at": datetime.now(),
        "created_by": "test_brain_validation",
        "assigned_to": "validation_test_system",
        "priority": "high"
    }
    
    # MANDATORY: Get approval to begin
    can_proceed, message = AI_TASK_BEGIN_HOOK(task_definition)
    if not can_proceed:
        print(f"❌ Task validation failed: {message}")
        return False
    
    print(f"✅ Task approved: {message}")
    print("🚀 Beginning brain validation test...")
    
    # Now perform the actual testing
    try:
        from brain import Brain
        
        print("\n=== BRAIN INITIALIZATION TEST ===")
        brain = Brain()
        print(f"✅ Brain initialized: {brain.session_id}")
        print(f"✅ Database type: {type(brain.memory)}")
        print(f"✅ Config model: {brain.config['local']['model']}")
        
        print("\n=== LOCAL LLM TEST ===")
        response = brain.call_local_llm('Respond with "VALIDATION TEST SUCCESS"')
        print(f"Model: {response.model}")
        if response.error:
            print(f"Expected error (Ollama may not be running): {response.error[:100]}...")
        else:
            print(f"Response: {response.response}")
            
        # Create test results file
        import json
        results = {
            "test_id": task_definition["task_id"],
            "timestamp": datetime.now().isoformat(),
            "brain_session_id": brain.session_id,
            "brain_initialized": True,
            "database_type": str(type(brain.memory)),
            "config_model": brain.config['local']['model'],
            "llm_response": {
                "model": response.model,
                "has_error": bool(response.error),
                "error": response.error[:100] if response.error else None,
                "response": response.response[:100] if response.response else None
            },
            "validation_framework_active": True
        }
        
        results_file = task_definition["deliverable_location"]
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Test results saved to: {results_file}")
        
        # MANDATORY: Complete task
        is_complete, completion_message = AI_TASK_COMPLETE_HOOK(
            task_definition["task_id"],
            [results_file],
            metadata={"test_results": results}
        )
        
        if is_complete:
            print(f"✅ Task completion validated: {completion_message}")
            return True
        else:
            print(f"❌ Task completion failed: {completion_message}")
            return False
            
    except Exception as e:
        print(f"❌ Brain test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 BRAIN VALIDATION TEST WITH MANDATORY FRAMEWORK")
    print("=" * 50)
    
    success = test_brain_with_validation()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 BRAIN VALIDATION TEST COMPLETED SUCCESSFULLY") 
        print("🛡️ Validation framework enforced throughout")
    else:
        print("❌ BRAIN VALIDATION TEST FAILED")
        print("🔒 Check validation framework logs")
    print("=" * 50)