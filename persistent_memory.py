#!/usr/bin/env python3
"""
PostgreSQL Persistent Memory Core - Enhanced memory system for Kurt's AI ecosystem
Identical API to SQLite version but with PostgreSQL backend + pgvector
"""

import os
import json
import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import threading
import logging
from contextlib import contextmanager
from pathlib import Path

# PostgreSQL imports
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False
    print("Warning: psycopg2 not available - PostgreSQL features disabled")

# Load environment configuration
from dotenv import load_dotenv
load_dotenv("/home/kurt/spatial-ai/.env")

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
logger = logging.getLogger(__name__)

class PersistentMemoryPostgres:
    """PostgreSQL-based persistent memory system with identical API to SQLite version"""
    
    def __init__(self, db_url: str = None):
        if not POSTGRES_AVAILABLE:
            raise ImportError("psycopg2 not available - cannot use PostgreSQL backend")
        
        # Database configuration
        self.db_url = db_url or self._build_db_url()
        self.session_state_path = os.getenv("SESSION_STATE_PATH", "/home/kurt/spatial-ai/data/session_state.json")
        self.memory_path = os.getenv("MEMORY_PATH", "/home/kurt/spatial-ai/data/conversations")
        self.consolidation_interval = int(os.getenv("MEMORY_CONSOLIDATION_INTERVAL", "24"))
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.session_state_path), exist_ok=True)
        os.makedirs(self.memory_path, exist_ok=True)
        
        self._lock = threading.Lock()
        self._session_cache = {}
        self._context_cache = {}
        
        self._init_database()
        self._load_session_state()
        
        logger.info(f"PostgreSQL Persistent Memory Core initialized - DB: {self.db_url}")
    
    def _build_db_url(self) -> str:
        """Build database URL from environment or default"""
        # Try to get from environment first
        db_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL")
        
        if db_url:
            return db_url
        
        # Build from components
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "spatial_ai")
        password = os.getenv("POSTGRES_PASSWORD", "spatial_ai_password")
        database = os.getenv("POSTGRES_DB", "spatial_constellation")
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def _init_database(self):
        """Initialize the PostgreSQL database schema"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                # Enable pgvector extension
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                
                # Create memory entries table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS memory_entries (
                        id SERIAL PRIMARY KEY,
                        session_id TEXT NOT NULL,
                        component TEXT NOT NULL,
                        context_hash TEXT NOT NULL,
                        entry_type TEXT NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        importance_score INTEGER DEFAULT 5,
                        access_count INTEGER DEFAULT 0,
                        embedding VECTOR(384) -- For future semantic search
                    )
                """)
                
                # Create session states table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS session_states (
                        session_id TEXT NOT NULL,
                        component TEXT NOT NULL,
                        state_data JSONB NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (session_id, component)
                    )
                """)
                
                # Create context links table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS context_links (
                        id SERIAL PRIMARY KEY,
                        from_context TEXT NOT NULL,
                        to_context TEXT NOT NULL,
                        link_type TEXT NOT NULL,
                        strength REAL DEFAULT 1.0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create memory archive table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS memory_archive (
                        LIKE memory_entries INCLUDING ALL
                    )
                """)
                
                # Create indexes for performance
                cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_session_component ON memory_entries(session_id, component)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_context_hash ON memory_entries(context_hash)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_importance ON memory_entries(importance_score)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_created_at ON memory_entries(created_at)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_session_states_lookup ON session_states(session_id, component)")
                cur.execute("CREATE INDEX IF NOT EXISTS idx_context_links_from ON context_links(from_context)")
                
                # Create vector similarity index (for future semantic search)
                cur.execute("CREATE INDEX IF NOT EXISTS idx_memory_embedding ON memory_entries USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")
                
                conn.commit()
    
    def _load_session_state(self):
        """Load session state from disk"""
        try:
            if os.path.exists(self.session_state_path):
                with open(self.session_state_path, 'r') as f:
                    self._session_cache = json.load(f)
            else:
                self._session_cache = {"current_session": self._generate_session_id()}
        except Exception as e:
            logger.warning(f"Failed to load session state: {e}")
            self._session_cache = {"current_session": self._generate_session_id()}
    
    def _save_session_state(self):
        """Save session state to disk"""
        try:
            with open(self.session_state_path, 'w') as f:
                json.dump(self._session_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session state: {e}")
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID"""
        return f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]}"
    
    def _generate_context_hash(self, component: str, context: str) -> str:
        """Generate a hash for context identification"""
        return hashlib.sha256(f"{component}:{context}".encode()).hexdigest()[:16]
    
    @contextmanager
    def get_db_connection(self):
        """Context manager for database connections"""
        conn = psycopg2.connect(self.db_url, cursor_factory=RealDictCursor)
        try:
            yield conn
        finally:
            conn.close()
    
    def store_memory(self, component: str, entry_type: str, content: str, 
                    context: str = "", metadata: Dict[str, Any] = None, 
                    importance: int = 5, session_id: str = None) -> str:
        """Store a memory entry with full context"""
        with self._lock:
            if session_id is None:
                session_id = self._session_cache.get("current_session", self._generate_session_id())
            
            context_hash = self._generate_context_hash(component, context)
            metadata_json = metadata or {}
            
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO memory_entries 
                        (session_id, component, context_hash, entry_type, content, metadata, importance_score)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (session_id, component, context_hash, entry_type, content, json.dumps(metadata_json), importance))
                    
                    entry_id = cur.fetchone()['id']
                    conn.commit()
                    
                    logger.debug(f"Stored memory entry {entry_id} for {component}:{entry_type}")
                    return str(entry_id)
    
    def retrieve_memory(self, component: str = None, entry_type: str = None, 
                       context: str = "", session_id: str = None, 
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve memory entries with optional filtering"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                query = "SELECT * FROM memory_entries WHERE 1=1"
                params = []
                
                if component:
                    query += " AND component = %s"
                    params.append(component)
                
                if entry_type:
                    query += " AND entry_type = %s"
                    params.append(entry_type)
                
                if context:
                    context_hash = self._generate_context_hash(component or "", context)
                    query += " AND context_hash = %s"
                    params.append(context_hash)
                
                if session_id:
                    query += " AND session_id = %s"
                    params.append(session_id)
                
                query += " ORDER BY importance_score DESC, created_at DESC"
                
                if limit:
                    query += " LIMIT %s"
                    params.append(limit)
                
                cur.execute(query, params)
                results = []
                
                for row in cur.fetchall():
                    entry = dict(row)
                    # Parse metadata JSON
                    if entry['metadata']:
                        entry['metadata'] = entry['metadata']  # Already parsed by RealDictCursor
                    else:
                        entry['metadata'] = {}
                    results.append(entry)
                
                # Update access count
                if results:
                    entry_ids = [str(r['id']) for r in results]
                    placeholders = ','.join(['%s'] * len(entry_ids))
                    cur.execute(f"""
                        UPDATE memory_entries 
                        SET access_count = access_count + 1, updated_at = CURRENT_TIMESTAMP
                        WHERE id IN ({placeholders})
                    """, entry_ids)
                    conn.commit()
                
                return results
    
    def store_session_state(self, component: str, state_data: Dict[str, Any], 
                          session_id: str = None) -> None:
        """Store session state for a component"""
        with self._lock:
            if session_id is None:
                session_id = self._session_cache.get("current_session", self._generate_session_id())
            
            with self.get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO session_states 
                        (session_id, component, state_data, updated_at)
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (session_id, component) 
                        DO UPDATE SET 
                            state_data = EXCLUDED.state_data,
                            updated_at = CURRENT_TIMESTAMP
                    """, (session_id, component, json.dumps(state_data)))
                    conn.commit()
            
            # Update cache
            cache_key = f"{session_id}:{component}"
            self._session_cache[cache_key] = state_data
            self._save_session_state()
            
            logger.debug(f"Stored session state for {component}")
    
    def retrieve_session_state(self, component: str, session_id: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve session state for a component"""
        if session_id is None:
            session_id = self._session_cache.get("current_session")
        
        cache_key = f"{session_id}:{component}"
        if cache_key in self._session_cache:
            return self._session_cache[cache_key]
        
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT state_data FROM session_states 
                    WHERE session_id = %s AND component = %s
                """, (session_id, component))
                
                row = cur.fetchone()
                if row:
                    state_data = row['state_data']
                    self._session_cache[cache_key] = state_data
                    return state_data
        
        return None
    
    def create_context_link(self, from_context: str, to_context: str, 
                          link_type: str = "related", strength: float = 1.0) -> None:
        """Create a link between contexts"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO context_links 
                    (from_context, to_context, link_type, strength)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (from_context, to_context, link_type, strength))
                conn.commit()
    
    def get_related_contexts(self, context: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get contexts related to the given context"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT to_context, link_type, strength 
                    FROM context_links 
                    WHERE from_context = %s 
                    ORDER BY strength DESC 
                    LIMIT %s
                """, (context, limit))
                
                return [dict(row) for row in cur.fetchall()]
    
    def consolidate_memory(self, older_than_hours: int = None) -> Dict[str, int]:
        """Consolidate and archive old memory entries"""
        if older_than_hours is None:
            older_than_hours = self.consolidation_interval
        
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                # Count entries to archive
                cur.execute("""
                    SELECT COUNT(*) as count FROM memory_entries 
                    WHERE created_at < %s AND importance_score < 3 AND access_count < 2
                """, (cutoff_time,))
                
                to_archive = cur.fetchone()['count']
                
                # Move to archive table
                cur.execute("""
                    INSERT INTO memory_archive 
                    SELECT * FROM memory_entries 
                    WHERE created_at < %s AND importance_score < 3 AND access_count < 2
                """, (cutoff_time,))
                
                cur.execute("""
                    DELETE FROM memory_entries 
                    WHERE created_at < %s AND importance_score < 3 AND access_count < 2
                """, (cutoff_time,))
                
                conn.commit()
                
                logger.info(f"Consolidated {to_archive} memory entries")
                return {"archived": to_archive}
    
    def get_current_session_id(self) -> str:
        """Get the current session ID"""
        return self._session_cache.get("current_session", self._generate_session_id())
    
    def start_new_session(self, component: str = None) -> str:
        """Start a new session"""
        with self._lock:
            new_session_id = self._generate_session_id()
            self._session_cache["current_session"] = new_session_id
            self._save_session_state()
            
            if component:
                self.store_memory(component, "session_start", f"New session started: {new_session_id}")
            
            logger.info(f"Started new session: {new_session_id}")
            return new_session_id
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        with self.get_db_connection() as conn:
            with conn.cursor() as cur:
                # Total entries
                cur.execute("SELECT COUNT(*) as count FROM memory_entries")
                total_entries = cur.fetchone()['count']
                
                # Entries by component
                cur.execute("""
                    SELECT component, COUNT(*) as count 
                    FROM memory_entries 
                    GROUP BY component 
                    ORDER BY count DESC
                """)
                by_component = {row['component']: row['count'] for row in cur.fetchall()}
                
                # Recent activity
                cur.execute("""
                    SELECT COUNT(*) as count FROM memory_entries 
                    WHERE created_at > CURRENT_TIMESTAMP - INTERVAL '1 day'
                """)
                recent_entries = cur.fetchone()['count']
                
                return {
                    "total_entries": total_entries,
                    "by_component": by_component,
                    "recent_entries": recent_entries,
                    "current_session": self.get_current_session_id(),
                    "db_url": self.db_url,
                    "backend": "postgresql"
                }

# Global instance
_memory_core = None

def get_memory_core() -> PersistentMemoryPostgres:
    """Get the global memory core instance"""
    global _memory_core
    if _memory_core is None:
        _memory_core = PersistentMemoryPostgres()
    return _memory_core

# Convenience functions for common operations
def store_memory(component: str, entry_type: str, content: str, **kwargs) -> str:
    """Store a memory entry"""
    return get_memory_core().store_memory(component, entry_type, content, **kwargs)

def retrieve_memory(component: str = None, **kwargs) -> List[Dict[str, Any]]:
    """Retrieve memory entries"""
    return get_memory_core().retrieve_memory(component, **kwargs)

def store_session_state(component: str, state_data: Dict[str, Any], **kwargs) -> None:
    """Store session state"""
    return get_memory_core().store_session_state(component, state_data, **kwargs)

def retrieve_session_state(component: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Retrieve session state"""
    return get_memory_core().retrieve_session_state(component, **kwargs)

if __name__ == "__main__":
    # Test the PostgreSQL memory system
    print("Testing PostgreSQL Persistent Memory System...")
    
    try:
        memory = get_memory_core()
        print("✅ PostgreSQL connection successful")
        
        # Store some test data
        memory.store_memory("test_component", "initialization", "PostgreSQL system started", importance=8)
        memory.store_memory("test_component", "user_interaction", "User tested PostgreSQL", context="migration_test")
        memory.store_memory("migration_system", "database_test", "PostgreSQL memory system working", 
                          metadata={"backend": "postgresql", "version": "16"})
        
        # Retrieve and display
        entries = memory.retrieve_memory("test_component")
        print(f"✅ Retrieved {len(entries)} entries")
        for entry in entries:
            print(f"  {entry['entry_type']}: {entry['content']}")
        
        # Store session state
        memory.store_session_state("test_component", {"active": True, "mode": "postgresql", "migration_step": 3})
        state = memory.retrieve_session_state("test_component")
        print(f"✅ Session state: {state}")
        
        # Show stats
        stats = memory.get_memory_stats()
        print(f"✅ Memory stats: {stats}")
        
        print("\n🎉 PostgreSQL Persistent Memory System is working!")
        
    except Exception as e:
        print(f"❌ Error testing PostgreSQL system: {e}")
        print("Make sure PostgreSQL is running and database is accessible")