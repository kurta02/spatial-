#!/usr/bin/env python3
"""
Database setup script for Spatial Constellation System
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import Config

def create_database():
    """Create the database if it doesn't exist"""
    try:
        # Connect to PostgreSQL (default database)
        conn = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            database="postgres"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{Config.POSTGRES_DB}'")
        exists = cursor.fetchone()
        
        if not exists:
            print(f"Creating database '{Config.POSTGRES_DB}'...")
            cursor.execute(f"CREATE DATABASE {Config.POSTGRES_DB}")
            print("Database created successfully!")
        else:
            print(f"Database '{Config.POSTGRES_DB}' already exists.")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Error creating database: {e}")
        return False
    
    return True

def enable_pgvector():
    """Enable pgvector extension"""
    try:
        conn = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            database=Config.POSTGRES_DB
        )
        cursor = conn.cursor()
        
        # Enable pgvector extension
        print("Enabling pgvector extension...")
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
        conn.commit()
        print("pgvector extension enabled!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Error enabling pgvector: {e}")
        print("Note: Make sure pgvector is installed on your system")
        return False
    
    return True

def create_tables():
    """Create necessary tables"""
    try:
        conn = psycopg2.connect(
            host=Config.POSTGRES_HOST,
            port=Config.POSTGRES_PORT,
            user=Config.POSTGRES_USER,
            password=Config.POSTGRES_PASSWORD,
            database=Config.POSTGRES_DB
        )
        cursor = conn.cursor()
        
        # Create memory_entries table
        print("Creating memory_entries table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_entries (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(255) NOT NULL,
                component VARCHAR(255) NOT NULL,
                entry_type VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                context VARCHAR(255),
                metadata JSONB,
                embedding vector(384),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_session ON memory_entries(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_component ON memory_entries(component)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_type ON memory_entries(entry_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_created ON memory_entries(created_at)")
        
        # Create vector similarity index
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_embedding ON memory_entries USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")
        
        # Create review_undo table for API wrapper
        print("Creating review_undo table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_undo (
                id SERIAL PRIMARY KEY,
                operation_type VARCHAR(255) NOT NULL,
                operation_data JSONB NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                session_id VARCHAR(255),
                status VARCHAR(50) DEFAULT 'pending'
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_session ON review_undo(session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_review_timestamp ON review_undo(timestamp)")
        
        conn.commit()
        print("Tables created successfully!")
        
        cursor.close()
        conn.close()
        
    except psycopg2.Error as e:
        print(f"Error creating tables: {e}")
        return False
    
    return True

def test_connection():
    """Test database connection and basic operations"""
    try:
        # Import the persistent memory module
        from core.persistent_memory import store_memory, retrieve_memory
        
        print("Testing database connection...")
        
        # Test storing a memory entry
        store_memory(
            component="setup_test",
            entry_type="test",
            content="Database setup test entry",
            context="test_context"
        )
        
        # Test retrieving memory entries
        entries = retrieve_memory(
            component="setup_test",
            entry_type="test",
            limit=1
        )
        
        if entries:
            print("Database connection test successful!")
            return True
        else:
            print("Database connection test failed - no entries retrieved")
            return False
            
    except Exception as e:
        print(f"Database connection test failed: {e}")
        return False

def main():
    """Main setup function"""
    print("=== Spatial Constellation Database Setup ===")
    print(f"Host: {Config.POSTGRES_HOST}:{Config.POSTGRES_PORT}")
    print(f"Database: {Config.POSTGRES_DB}")
    print(f"User: {Config.POSTGRES_USER}")
    print()
    
    # Validate configuration
    try:
        Config.validate_config()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        return False
    
    # Create directories
    Config.ensure_directories()
    print("Created necessary directories.")
    
    # Setup database
    steps = [
        ("Creating database", create_database),
        ("Enabling pgvector extension", enable_pgvector),
        ("Creating tables", create_tables),
        ("Testing connection", test_connection)
    ]
    
    for step_name, step_func in steps:
        print(f"\n{step_name}...")
        if not step_func():
            print(f"Failed at step: {step_name}")
            return False
    
    print("\n✅ Database setup completed successfully!")
    print("\nNext steps:")
    print("1. Copy .env.example to .env and configure your API keys")
    print("2. Run: python scripts/start_system.py")
    print("3. Or launch the CLI: python core/conversational_cli.py")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)