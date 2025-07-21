#!/usr/bin/env python3
"""
Memory Migration Test - Compare SQLite vs PostgreSQL systems
Verifies both systems have identical APIs and behavior
"""

import sys
import os
sys.path.insert(0, '/home/kurt/spatial-ai')
sys.path.insert(0, '/home/kurt/migration-workspace')

from persistent_memory_core import PersistentMemoryCore as SQLiteMemory
from persistent_memory_postgres import PersistentMemoryPostgres

def test_memory_systems():
    """Test both memory systems with identical operations"""
    
    print("🧪 Memory Migration Test")
    print("=" * 50)
    
    # Initialize both systems
    print("\n1. Initializing memory systems...")
    sqlite_memory = SQLiteMemory()
    postgres_memory = PersistentMemoryPostgres()
    
    print(f"   SQLite: {sqlite_memory.db_path}")
    print(f"   PostgreSQL: {postgres_memory.db_url}")
    
    # Test data storage
    print("\n2. Testing data storage...")
    test_data = [
        ("migration_test", "sqlite_test", "Testing SQLite storage", {"test": "sqlite"}),
        ("migration_test", "postgres_test", "Testing PostgreSQL storage", {"test": "postgres"}),
        ("migration_test", "comparison", "Both systems working", {"importance": "high"})
    ]
    
    sqlite_ids = []
    postgres_ids = []
    
    for component, entry_type, content, metadata in test_data:
        sqlite_id = sqlite_memory.store_memory(component, entry_type, content, metadata=metadata)
        postgres_id = postgres_memory.store_memory(component, entry_type, content, metadata=metadata)
        
        sqlite_ids.append(sqlite_id)
        postgres_ids.append(postgres_id)
        
        print(f"   ✅ {entry_type}: SQLite ID {sqlite_id}, PostgreSQL ID {postgres_id}")
    
    # Test data retrieval
    print("\n3. Testing data retrieval...")
    sqlite_entries = sqlite_memory.retrieve_memory("migration_test")
    postgres_entries = postgres_memory.retrieve_memory("migration_test")
    
    print(f"   SQLite retrieved: {len(sqlite_entries)} entries")
    print(f"   PostgreSQL retrieved: {len(postgres_entries)} entries")
    
    # Compare content
    sqlite_content = [e['content'] for e in sqlite_entries]
    postgres_content = [e['content'] for e in postgres_entries]
    
    content_match = set(sqlite_content) == set(postgres_content)
    print(f"   Content match: {'✅' if content_match else '❌'}")
    
    # Test session state
    print("\n4. Testing session state...")
    test_state = {
        "migration_active": True,
        "step": 3,
        "backend_test": "passed",
        "timestamp": "2025-07-18"
    }
    
    sqlite_memory.store_session_state("migration_test", test_state)
    postgres_memory.store_session_state("migration_test", test_state)
    
    sqlite_state = sqlite_memory.retrieve_session_state("migration_test")
    postgres_state = postgres_memory.retrieve_session_state("migration_test")
    
    state_match = sqlite_state == postgres_state
    print(f"   Session state match: {'✅' if state_match else '❌'}")
    print(f"   SQLite state: {sqlite_state}")
    print(f"   PostgreSQL state: {postgres_state}")
    
    # Test statistics
    print("\n5. Testing statistics...")
    sqlite_stats = sqlite_memory.get_memory_stats()
    postgres_stats = postgres_memory.get_memory_stats()
    
    print(f"   SQLite total: {sqlite_stats['total_entries']}")
    print(f"   PostgreSQL total: {postgres_stats['total_entries']}")
    print(f"   SQLite backend: {sqlite_stats.get('backend', 'sqlite')}")
    print(f"   PostgreSQL backend: {postgres_stats.get('backend', 'unknown')}")
    
    # API compatibility test
    print("\n6. Testing API compatibility...")
    api_tests = []
    
    # Test identical function signatures
    try:
        # Both should support same parameters
        sqlite_memory.store_memory("api_test", "test", "content", context="test", importance=7)
        postgres_memory.store_memory("api_test", "test", "content", context="test", importance=7)
        api_tests.append(("store_memory signature", True))
    except Exception as e:
        api_tests.append(("store_memory signature", False))
    
    try:
        # Both should support same retrieval parameters
        sqlite_memory.retrieve_memory("api_test", entry_type="test", limit=10)
        postgres_memory.retrieve_memory("api_test", entry_type="test", limit=10)
        api_tests.append(("retrieve_memory signature", True))
    except Exception as e:
        api_tests.append(("retrieve_memory signature", False))
    
    for test_name, passed in api_tests:
        print(f"   {test_name}: {'✅' if passed else '❌'}")
    
    # Performance comparison
    print("\n7. Performance comparison...")
    import time
    
    # SQLite performance
    start_time = time.time()
    for i in range(10):
        sqlite_memory.store_memory("perf_test", "entry", f"Performance test {i}")
    sqlite_time = time.time() - start_time
    
    # PostgreSQL performance
    start_time = time.time()
    for i in range(10):
        postgres_memory.store_memory("perf_test", "entry", f"Performance test {i}")
    postgres_time = time.time() - start_time
    
    print(f"   SQLite 10 inserts: {sqlite_time:.3f}s")
    print(f"   PostgreSQL 10 inserts: {postgres_time:.3f}s")
    print(f"   Performance ratio: {postgres_time/sqlite_time:.2f}x")
    
    # Migration readiness assessment
    print("\n8. Migration readiness assessment...")
    
    checks = [
        ("API compatibility", all(result for _, result in api_tests)),
        ("Data storage", len(sqlite_ids) == len(postgres_ids)),
        ("Data retrieval", content_match),
        ("Session state", state_match),
        ("PostgreSQL connection", postgres_stats['backend'] == 'postgresql'),
        ("SQLite fallback", sqlite_stats['total_entries'] > 0)
    ]
    
    all_passed = all(passed for _, passed in checks)
    
    for check_name, passed in checks:
        print(f"   {check_name}: {'✅' if passed else '❌'}")
    
    print(f"\n🎯 Migration readiness: {'✅ READY' if all_passed else '❌ NOT READY'}")
    
    if all_passed:
        print("\n✅ Both memory systems are working and compatible!")
        print("✅ Ready to proceed with Step 4: API integration")
        return True
    else:
        print("\n❌ Issues found - need to resolve before proceeding")
        return False

if __name__ == "__main__":
    success = test_memory_systems()
    sys.exit(0 if success else 1)