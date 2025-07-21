#!/usr/bin/env python3
"""
Persistent Memory Core - Universal memory system for Kurt's AI ecosystem
Handles global state, context persistence, and cross-session memory
"""

import os
import json
import sqlite3
import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import threading
import logging
from contextlib import contextmanager
from pathlib import Path

# Load environment configuration
from dotenv import load_dotenv
load_dotenv("/home/kurt/spatial-ai/.env")

logging.basicConfig(level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
logger = logging.getLogger(__name__)

class PersistentMemoryCore:
    """Universal persistent memory system for all AI components"""
    
    def __init__(self):
        self.db_path = os.getenv("PERSISTENT_MEMORY_DB", "/home/kurt/spatial-ai/data/global_memory.db")
        self.session_state_path = os.getenv("SESSION_STATE_PATH", "/home/kurt/spatial-ai/data/session_state.json")
        self.memory_path = os.getenv("MEMORY_PATH", "/home/kurt/spatial-ai/data/conversations")
        self.consolidation_interval = int(os.getenv("MEMORY_CONSOLIDATION_INTERVAL", "24"))
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.session_state_path), exist_ok=True)
        os.makedirs(self.memory_path, exist_ok=True)
        
        self._lock = threading.Lock()
        self._session_cache = {}
        self._context_cache = {}
        
        self._init_database()
        self._load_session_state()
        
        logger.info(f"Persistent Memory Core initialized - DB: {self.db_path}")
    
    def _init_database(self):
        """Initialize the SQLite database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    component TEXT NOT NULL,
                    context_hash TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    importance_score INTEGER DEFAULT 5,
                    access_count INTEGER DEFAULT 0
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS session_states (
                    session_id TEXT PRIMARY KEY,
                    component TEXT NOT NULL,
                    state_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS context_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_context TEXT NOT NULL,
                    to_context TEXT NOT NULL,
                    link_type TEXT NOT NULL,
                    strength REAL DEFAULT 1.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_component ON memory_entries(session_id, component)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_context_hash ON memory_entries(context_hash)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_importance ON memory_entries(importance_score)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_session_states ON session_states(session_id, component)")
            
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
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
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
            metadata_json = json.dumps(metadata or {})
            
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO memory_entries 
                    (session_id, component, context_hash, entry_type, content, metadata, importance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (session_id, component, context_hash, entry_type, content, metadata_json, importance))
                
                entry_id = cursor.lastrowid
                conn.commit()
                
                logger.debug(f"Stored memory entry {entry_id} for {component}:{entry_type}")
                return str(entry_id)
    
    def retrieve_memory(self, component: str = None, entry_type: str = None, 
                       context: str = "", session_id: str = None, 
                       limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve memory entries with optional filtering"""
        with self.get_db_connection() as conn:
            query = "SELECT * FROM memory_entries WHERE 1=1"
            params = []
            
            if component:
                query += " AND component = ?"
                params.append(component)
            
            if entry_type:
                query += " AND entry_type = ?"
                params.append(entry_type)
            
            if context:
                context_hash = self._generate_context_hash(component or "", context)
                query += " AND context_hash = ?"
                params.append(context_hash)
            
            if session_id:
                query += " AND session_id = ?"
                params.append(session_id)
            
            query += " ORDER BY importance_score DESC, created_at DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                entry = dict(row)
                entry['metadata'] = json.loads(entry['metadata'] or '{}')
                results.append(entry)
            
            # Update access count
            if results:
                entry_ids = [str(r['id']) for r in results]
                conn.execute(f"""
                    UPDATE memory_entries 
                    SET access_count = access_count + 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id IN ({','.join(['?'] * len(entry_ids))})
                """, entry_ids)
                conn.commit()
            
            return results
    
    def store_session_state(self, component: str, state_data: Dict[str, Any], 
                          session_id: str = None) -> None:
        """Store session state for a component"""
        with self._lock:
            if session_id is None:
                session_id = self._session_cache.get("current_session", self._generate_session_id())
            
            state_json = json.dumps(state_data)
            
            with self.get_db_connection() as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO session_states 
                    (session_id, component, state_data, updated_at)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """, (session_id, component, state_json))
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
            cursor = conn.cursor()
            cursor.execute("""
                SELECT state_data FROM session_states 
                WHERE session_id = ? AND component = ?
            """, (session_id, component))
            
            row = cursor.fetchone()
            if row:
                state_data = json.loads(row['state_data'])
                self._session_cache[cache_key] = state_data
                return state_data
        
        return None
    
    def create_context_link(self, from_context: str, to_context: str, 
                          link_type: str = "related", strength: float = 1.0) -> None:
        """Create a link between contexts"""
        with self.get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO context_links 
                (from_context, to_context, link_type, strength)
                VALUES (?, ?, ?, ?)
            """, (from_context, to_context, link_type, strength))
            conn.commit()
    
    def get_related_contexts(self, context: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get contexts related to the given context"""
        with self.get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT to_context, link_type, strength 
                FROM context_links 
                WHERE from_context = ? 
                ORDER BY strength DESC 
                LIMIT ?
            """, (context, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def consolidate_memory(self, older_than_hours: int = None) -> Dict[str, int]:
        """Consolidate and archive old memory entries"""
        if older_than_hours is None:
            older_than_hours = self.consolidation_interval
        
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        
        with self.get_db_connection() as conn:
            # Archive low-importance, old entries
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM memory_entries 
                WHERE created_at < ? AND importance_score < 3 AND access_count < 2
            """, (cutoff_time,))
            
            to_archive = cursor.fetchone()[0]
            
            # Move to archive table (create if not exists)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_archive AS 
                SELECT * FROM memory_entries WHERE 1=0
            """)
            
            conn.execute("""
                INSERT INTO memory_archive 
                SELECT * FROM memory_entries 
                WHERE created_at < ? AND importance_score < 3 AND access_count < 2
            """, (cutoff_time,))
            
            conn.execute("""
                DELETE FROM memory_entries 
                WHERE created_at < ? AND importance_score < 3 AND access_count < 2
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
            cursor = conn.cursor()
            
            # Total entries
            cursor.execute("SELECT COUNT(*) FROM memory_entries")
            total_entries = cursor.fetchone()[0]
            
            # Entries by component
            cursor.execute("""
                SELECT component, COUNT(*) as count 
                FROM memory_entries 
                GROUP BY component 
                ORDER BY count DESC
            """)
            by_component = dict(cursor.fetchall())
            
            # Recent activity
            cursor.execute("""
                SELECT COUNT(*) FROM memory_entries 
                WHERE created_at > datetime('now', '-1 day')
            """)
            recent_entries = cursor.fetchone()[0]
            
            return {
                "total_entries": total_entries,
                "by_component": by_component,
                "recent_entries": recent_entries,
                "current_session": self.get_current_session_id(),
                "db_path": self.db_path
            }

# Global instance
_memory_core = None

def get_memory_core() -> PersistentMemoryCore:
    """Get the global memory core instance"""
    global _memory_core
    if _memory_core is None:
        _memory_core = PersistentMemoryCore()
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
    # Test the memory system
    memory = get_memory_core()
    
    # Store some test data
    memory.store_memory("test_component", "initialization", "System started", importance=8)
    memory.store_memory("test_component", "user_interaction", "User said hello", context="conversation_1")
    memory.store_memory("brain_system", "llm_call", "Called OpenAI GPT-4", metadata={"model": "gpt-4", "tokens": 150})
    
    # Retrieve and display
    entries = memory.retrieve_memory("test_component")
    print(f"Retrieved {len(entries)} entries")
    for entry in entries:
        print(f"  {entry['entry_type']}: {entry['content']}")
    
    # Store session state
    memory.store_session_state("test_component", {"active": True, "mode": "interactive"})
    state = memory.retrieve_session_state("test_component")
    print(f"Session state: {state}")
    
    # Show stats
    stats = memory.get_memory_stats()
    print(f"Memory stats: {stats}")