#!/usr/bin/env python3
"""
Spatial Constellation System Startup Script

This script initializes and starts the complete spatial constellation system
with Manus's advanced agent coordination.
"""

import os
import sys
import json
import logging
import subprocess
from pathlib import Path

def setup_environment():
    """Setup the Python environment and paths"""
    # Add src to Python path
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    print("✅ Python environment configured")

def check_dependencies():
    """Check if required dependencies are available"""
    required_packages = ['requests', 'sqlite3', 'flask']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {missing_packages}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All required packages available")
    return True

def check_ollama():
    """Check if Ollama is running and available"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✅ Ollama available with {len(models)} models")
            return True
        else:
            print("❌ Ollama not responding")
            return False
    except Exception as e:
        print(f"❌ Ollama not available: {e}")
        return False

def initialize_memory_system():
    """Initialize the persistent memory system"""
    try:
        from memory.persistent_memory import PersistentMemory
        
        # Create data directory
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Initialize memory
        memory = PersistentMemory(data_dir="data")
        
        # Store initialization record
        memory.store_memory(
            component="system",
            entry_type="initialization",
            content="Spatial Constellation System started successfully",
            importance=9
        )
        
        print(f"✅ Memory system initialized - Session: {memory.session_id}")
        return memory.session_id
        
    except Exception as e:
        print(f"❌ Memory system initialization failed: {e}")
        return None

def initialize_agent_coordinator():
    """Initialize the local agent coordinator"""
    try:
        from core.local_agent_coordinator import LocalAgentCoordinator
        
        coordinator = LocalAgentCoordinator()
        
        # Test basic functionality
        test_task_id = coordinator.create_task("System initialization test")
        result = coordinator.execute_task(test_task_id)
        
        if result.get('success'):
            print("✅ Agent coordinator initialized and tested")
            return coordinator
        else:
            print(f"❌ Agent coordinator test failed: {result.get('error')}")
            return None
            
    except Exception as e:
        print(f"❌ Agent coordinator initialization failed: {e}")
        return None

def start_flask_api():
    """Start the Flask API server"""
    try:
        # Check if Flask API exists
        api_file = Path("api/app.py")
        if api_file.exists():
            print("🚀 Starting Flask API server...")
            # Could start Flask server here if needed
            print("✅ Flask API ready (manual start required)")
        else:
            print("ℹ️  Flask API not found - using basic coordination only")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask API startup failed: {e}")
        return False

def display_system_status(session_id, coordinator):
    """Display the system status"""
    print("\n" + "="*50)
    print("🌟 SPATIAL CONSTELLATION SYSTEM READY")
    print("="*50)
    
    if session_id:
        print(f"📊 Memory Session: {session_id}")
    
    if coordinator:
        status = coordinator.get_status()
        print(f"🤖 Agent Coordinator: {status['session_id']}")
        print(f"🎯 Agents Available: {status['agents_available']}")
        print(f"💰 Total Cost: ${status['total_cost']:.4f}")
    
    print("\nNext Steps:")
    print("1. Use the agent coordinator for task execution")
    print("2. Access persistent memory for session continuity")
    print("3. Monitor costs with local-first approach")
    print("4. Check logs in data/ directory")
    
    print("\nExample Usage:")
    print("from core.local_agent_coordinator import LocalAgentCoordinator")
    print("coordinator = LocalAgentCoordinator()")
    print('task_id = coordinator.create_task("Your task here")')
    print("result = coordinator.execute_task(task_id)")

def main():
    """Main startup sequence"""
    print("🚀 Starting Spatial Constellation System...")
    print("Integrating Manus's advanced agent coordination\n")
    
    # Setup environment
    setup_environment()
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ System startup failed - missing dependencies")
        return 1
    
    # Check Ollama (not required but recommended)
    ollama_available = check_ollama()
    
    # Initialize components
    session_id = initialize_memory_system()
    coordinator = initialize_agent_coordinator()
    
    # Start API server
    start_flask_api()
    
    # Display status
    if session_id and coordinator:
        display_system_status(session_id, coordinator)
        print("\n✅ System startup completed successfully!")
        return 0
    else:
        print("\n❌ System startup completed with errors")
        return 1

if __name__ == "__main__":
    exit_code = main()