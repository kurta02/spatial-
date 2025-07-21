#!/usr/bin/env python3
"""
Migration tools for Spatial Constellation System
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def backup_existing_system():
    """Create backup of existing spatial-ai system"""
    source_dir = Path("/home/kurt/spatial-ai")
    backup_dir = Path("/home/kurt/spatial-ai-backup-" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    
    if source_dir.exists():
        print(f"Creating backup: {backup_dir}")
        shutil.copytree(source_dir, backup_dir)
        print("Backup created successfully!")
        return backup_dir
    else:
        print("No existing spatial-ai system found to backup.")
        return None

def migrate_memory_data():
    """Migrate memory data from SQLite to PostgreSQL"""
    try:
        # Import both memory systems
        sys.path.insert(0, "/home/kurt/spatial-ai")
        from persistent_memory_core import retrieve_memory as sqlite_retrieve
        
        from core.persistent_memory import store_memory as postgres_store
        
        print("Migrating memory data from SQLite to PostgreSQL...")
        
        # Get all entries from SQLite
        entries = sqlite_retrieve(component="", entry_type="", context="", limit=1000)
        
        migrated_count = 0
        for entry in entries:
            try:
                # Store in PostgreSQL
                postgres_store(
                    component=entry.get('component', 'migrated'),
                    entry_type=entry.get('entry_type', 'unknown'),
                    content=entry.get('content', ''),
                    context=entry.get('context', ''),
                    metadata=entry.get('metadata', {}),
                    session_id=entry.get('session_id', 'migration')
                )
                migrated_count += 1
            except Exception as e:
                print(f"Failed to migrate entry {entry.get('id', 'unknown')}: {e}")
        
        print(f"Successfully migrated {migrated_count} memory entries.")
        return migrated_count
        
    except Exception as e:
        print(f"Memory migration failed: {e}")
        return 0

def copy_configuration():
    """Copy configuration from existing system"""
    source_configs = [
        "/home/kurt/spatial-ai/.env",
        "/home/kurt/Assistant/coordinator/config/config.py",
        "/home/kurt/whisper.cpp/llm_config.json"
    ]
    
    target_dir = Path(__file__).parent.parent
    
    for config_path in source_configs:
        source = Path(config_path)
        if source.exists():
            if source.name == ".env":
                target = target_dir / ".env"
                if not target.exists():  # Don't overwrite existing .env
                    shutil.copy2(source, target)
                    print(f"Copied: {source} -> {target}")
            elif source.name == "llm_config.json":
                target = target_dir / "config" / "llm_config.json"
                # Merge with existing config
                merge_llm_config(source, target)
        else:
            print(f"Config not found: {config_path}")

def merge_llm_config(source_path, target_path):
    """Merge LLM configuration files"""
    try:
        # Load source config
        with open(source_path, 'r') as f:
            source_config = json.load(f)
        
        # Load target config
        with open(target_path, 'r') as f:
            target_config = json.load(f)
        
        # Merge configurations (target takes precedence)
        merged_config = {**source_config, **target_config}
        
        # Write merged config
        with open(target_path, 'w') as f:
            json.dump(merged_config, f, indent=2)
        
        print(f"Merged LLM config: {source_path} -> {target_path}")
        
    except Exception as e:
        print(f"Failed to merge LLM config: {e}")

def validate_migration():
    """Validate the migration was successful"""
    checks = [
        ("Database connection", check_database),
        ("Memory system", check_memory_system),
        ("Configuration", check_configuration),
        ("File structure", check_file_structure)
    ]
    
    all_passed = True
    for check_name, check_func in checks:
        try:
            result = check_func()
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{check_name}: {status}")
            if not result:
                all_passed = False
        except Exception as e:
            print(f"{check_name}: ❌ FAIL ({e})")
            all_passed = False
    
    return all_passed

def check_database():
    """Check database connectivity"""
    try:
        from core.persistent_memory import test_connection
        return test_connection()
    except:
        return False

def check_memory_system():
    """Check memory system functionality"""
    try:
        from core.persistent_memory import store_memory, retrieve_memory
        
        # Test store
        store_memory(
            component="migration_test",
            entry_type="validation",
            content="Migration validation test",
            context="test"
        )
        
        # Test retrieve
        entries = retrieve_memory(
            component="migration_test",
            entry_type="validation",
            limit=1
        )
        
        return len(entries) > 0
    except:
        return False

def check_configuration():
    """Check configuration files"""
    required_files = [
        "config/config.py",
        "config/llm_config.json",
        ".env"
    ]
    
    project_dir = Path(__file__).parent.parent
    for file_path in required_files:
        if not (project_dir / file_path).exists():
            return False
    
    return True

def check_file_structure():
    """Check file structure is correct"""
    required_dirs = [
        "core", "api", "config", "scripts", "tests", "docs", "data"
    ]
    
    project_dir = Path(__file__).parent.parent
    for dir_name in required_dirs:
        if not (project_dir / dir_name).is_dir():
            return False
    
    return True

def create_migration_report():
    """Create migration report"""
    report = {
        "migration_date": datetime.now().isoformat(),
        "source_system": "/home/kurt/spatial-ai",
        "target_system": str(Path(__file__).parent.parent),
        "validation_results": {},
        "next_steps": [
            "Configure API keys in .env file",
            "Test conversational CLI",
            "Test Flask API endpoints",
            "Run full system test suite"
        ]
    }
    
    # Run validation
    checks = [
        ("database", check_database),
        ("memory_system", check_memory_system),
        ("configuration", check_configuration),
        ("file_structure", check_file_structure)
    ]
    
    for check_name, check_func in checks:
        try:
            report["validation_results"][check_name] = check_func()
        except Exception as e:
            report["validation_results"][check_name] = f"Error: {e}"
    
    # Write report
    report_path = Path(__file__).parent.parent / "data" / "migration_report.json"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Migration report saved: {report_path}")
    return report

def main():
    """Main migration function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Spatial Constellation Migration Tools")
    parser.add_argument("action", choices=[
        "backup", "migrate", "validate", "report", "full"
    ], help="Migration action to perform")
    
    args = parser.parse_args()
    
    if args.action == "backup":
        backup_existing_system()
    
    elif args.action == "migrate":
        print("Starting memory data migration...")
        migrated = migrate_memory_data()
        print(f"Migration complete: {migrated} entries migrated.")
    
    elif args.action == "validate":
        print("Validating migration...")
        success = validate_migration()
        if success:
            print("✅ All validation checks passed!")
        else:
            print("❌ Some validation checks failed.")
            sys.exit(1)
    
    elif args.action == "report":
        print("Generating migration report...")
        report = create_migration_report()
        print("Report generated successfully!")
    
    elif args.action == "full":
        print("Performing full migration...")
        backup_existing_system()
        copy_configuration()
        migrate_memory_data()
        create_migration_report()
        
        print("\n✅ Full migration complete!")
        print("Next steps:")
        print("1. Review and update .env file with your API keys")
        print("2. Run: ./scripts/start_system.sh")
        print("3. Test the system with: python core/conversational_cli.py")

if __name__ == "__main__":
    main()