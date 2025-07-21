#!/usr/bin/env python3
"""Test imports for Flask API"""

import sys
import os

# Add paths for imports
sys.path.insert(0, '/home/kurt/spatial-ai')
sys.path.insert(0, '/home/kurt/migration-workspace')

print("Testing imports...")

try:
    from flask import Flask, request, jsonify, Response
    print("✅ Flask imports OK")
except Exception as e:
    print(f"❌ Flask imports failed: {e}")

try:
    from flask_cors import CORS
    print("✅ Flask-CORS imports OK")  
except Exception as e:
    print(f"❌ Flask-CORS imports failed: {e}")

try:
    # Import orchestrator and memory systems
    from unified_orchestrator import UnifiedOrchestrator
    print("✅ UnifiedOrchestrator import OK")
except Exception as e:
    print(f"❌ UnifiedOrchestrator import failed: {e}")

try:
    from persistent_memory_postgres import PersistentMemoryPostgres
    print("✅ PersistentMemoryPostgres import OK")
except Exception as e:
    print(f"❌ PersistentMemoryPostgres import failed: {e}")

try:
    # Load environment configuration
    from dotenv import load_dotenv
    load_dotenv("/home/kurt/spatial-ai/.env")
    print("✅ Environment loading OK")
except Exception as e:
    print(f"❌ Environment loading failed: {e}")

print("\nTesting orchestrator initialization...")
try:
    orchestrator = UnifiedOrchestrator()
    print("✅ Orchestrator created successfully")
except Exception as e:
    print(f"❌ Orchestrator creation failed: {e}")
    import traceback
    traceback.print_exc()

print("✅ All tests complete")