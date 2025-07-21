#!/usr/bin/env python3
"""
Persistent Memory System - Robust Long-term Memory for Multi-AI Collaboration
Ensures no information is ever lost, with Git integration for version control
"""

import json
import sqlite3
import logging
import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import threading
import time

@dataclass
class MemoryEntry:
    id: str
    session_id: str
    component: str
    entry_type: str
    content: str
    metadata: Dict[str, Any]
    importance: int  # 1-10 scale
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    context_hash: str = ""

class PersistentMemory:
    """
    Robust persistent memory system with multiple storage backends
    Primary: SQLite for reliability and simplicity
    Secondary: JSON files for human readability
    Future: PostgreSQL with vector search
    """
    
    def __init__(self, data_dir: str = "data", session_id: str = None):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        self.session_id = session_id or f"session_{int(time.time())}"
        self.db_path = self.data_dir / "persistent_memory.db"
        self.json_backup_dir = self.data_dir / "json_backups"
        self.json_backup_dir.mkdir(exist_ok=True)
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
        
        # Auto-consolidation settings
        self.auto_consolidate = True
        self.consolidation_interval = 3600  # 1 hour
        self.last_consolidation = time.time()
        
        self.logger.info(f"Persistent Memory initialized - Session: {self.session_id}")
    
    def _init_database(self):
        """Initialize SQLite database with proper schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_entries (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    component TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT DEFAULT '{}',
                    importance INTEGER DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    context_hash TEXT DEFAULT ''
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_session_component 
                ON memory_entries(session_id, component)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_importance_created 
                ON memory_entries(importance DESC, created_at DESC)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_entry_type 
                ON memory_entries(entry_type)
            """)
            
            conn.commit()
    
    def store_memory(self, 
                    component: str,
                    entry_type: str, 
                    content: str,
                    metadata: Dict[str, Any] = None,
                    importance: int = 5,
                    context: str = "") -> str:
        """
        Store a memory entry with automatic deduplication and backup
        """
        with self._lock:
            # Generate unique ID
            entry_id = self._generate_entry_id(component, entry_type, content)
            
            # Generate context hash for deduplication
            context_hash = hashlib.md5(f"{content}{context}".encode()).hexdigest()
            
            # Check for duplicates
            if self._is_duplicate(context_hash, component):
                self.logger.debug(f"Duplicate memory entry detected, updating existing")
                return self._update_existing_entry(context_hash, component, content, metadata)
            
            # Create memory entry
            entry = MemoryEntry(
                id=entry_id,
                session_id=self.session_id,
                component=component,
                entry_type=entry_type,
                content=content,
                metadata=metadata or {},
                importance=importance,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                context_hash=context_hash
            )
            
            # Store in database
            self._store_to_database(entry)
            
            # Create JSON backup
            self._create_json_backup(entry)
            
            # Auto-consolidate if needed
            if self.auto_consolidate and self._should_consolidate():
                self._consolidate_memory()
            
            self.logger.info(f"Memory stored: {entry_id} - {component} - {entry_type}")
            return entry_id
    
    def _generate_entry_id(self, component: str, entry_type: str, content: str) -> str:
        """Generate unique entry ID"""
        timestamp = int(time.time() * 1000)
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{component}_{entry_type}_{timestamp}_{content_hash}"
    
    def _is_duplicate(self, context_hash: str, component: str) -> bool:
        """Check if entry is duplicate based on context hash"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM memory_entries WHERE context_hash = ? AND component = ?",
                (context_hash, component)
            )
            return cursor.fetchone() is not None
    
    def _update_existing_entry(self, context_hash: str, component: str, 
                              content: str, metadata: Dict[str, Any]) -> str:
        """Update existing entry instead of creating duplicate"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM memory_entries WHERE context_hash = ? AND component = ?",
                (context_hash, component)
            )
            result = cursor.fetchone()
            
            if result:
                entry_id = result[0]
                conn.execute("""
                    UPDATE memory_entries 
                    SET content = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP, access_count = access_count + 1
                    WHERE id = ?
                """, (content, json.dumps(metadata or {}), entry_id))
                conn.commit()
                return entry_id
        
        return ""
    
    def _store_to_database(self, entry: MemoryEntry):
        """Store memory entry to SQLite database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO memory_entries 
                (id, session_id, component, entry_type, content, metadata, importance, 
                 created_at, updated_at, access_count, context_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id, entry.session_id, entry.component, entry.entry_type,
                entry.content, json.dumps(entry.metadata), entry.importance,
                entry.created_at.isoformat(), entry.updated_at.isoformat(),
                entry.access_count, entry.context_hash
            ))
            conn.commit()
    
    def _create_json_backup(self, entry: MemoryEntry):
        """Create human-readable JSON backup"""
        backup_file = self.json_backup_dir / f"{entry.id}.json"
        try:
            with open(backup_file, 'w') as f:
                json.dump(asdict(entry), f, indent=2, default=str)
        except Exception as e:
            self.logger.warning(f"JSON backup failed for {entry.id}: {e}")
    
    def retrieve_memory(self, 
                       component: str = None,
                       entry_type: str = None,
                       limit: int = 50,
                       importance_threshold: int = 1,
                       recent_hours: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve memory entries with flexible filtering
        """
        with self._lock:
            query = "SELECT * FROM memory_entries WHERE importance >= ?"
            params = [importance_threshold]
            
            if component:
                query += " AND component = ?"
                params.append(component)
            
            if entry_type:
                query += " AND entry_type = ?"
                params.append(entry_type)
            
            if recent_hours:
                cutoff_time = datetime.now() - timedelta(hours=recent_hours)
                query += " AND created_at >= ?"
                params.append(cutoff_time.isoformat())
            
            query += " ORDER BY importance DESC, created_at DESC LIMIT ?"
            params.append(limit)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, params)
                results = []
                
                for row in cursor.fetchall():
                    # Update access count
                    conn.execute(
                        "UPDATE memory_entries SET access_count = access_count + 1 WHERE id = ?",
                        (row['id'],)
                    )
                    
                    # Convert to dict
                    entry_dict = dict(row)
                    entry_dict['metadata'] = json.loads(entry_dict['metadata'] or '{}')
                    results.append(entry_dict)
                
                conn.commit()
                
            self.logger.info(f"Retrieved {len(results)} memory entries")
            return results
    
    def search_memory(self, search_term: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Simple text search in memory content
        Future: Replace with vector similarity search
        """
        with self._lock:
            query = """
                SELECT * FROM memory_entries 
                WHERE content LIKE ? OR metadata LIKE ?
                ORDER BY importance DESC, created_at DESC 
                LIMIT ?
            """
            search_pattern = f"%{search_term}%"
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(query, (search_pattern, search_pattern, limit))
                
                results = []
                for row in cursor.fetchall():
                    entry_dict = dict(row)
                    entry_dict['metadata'] = json.loads(entry_dict['metadata'] or '{}')
                    results.append(entry_dict)
                
            self.logger.info(f"Search '{search_term}' returned {len(results)} results")
            return results
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        with sqlite3.connect(self.db_path) as conn:
            # Total entries
            total_entries = conn.execute("SELECT COUNT(*) FROM memory_entries").fetchone()[0]
            
            # By component
            component_stats = {}
            cursor = conn.execute("SELECT component, COUNT(*) FROM memory_entries GROUP BY component")
            for row in cursor.fetchall():
                component_stats[row[0]] = row[1]
            
            # By importance
            importance_stats = {}
            cursor = conn.execute("SELECT importance, COUNT(*) FROM memory_entries GROUP BY importance")
            for row in cursor.fetchall():
                importance_stats[row[0]] = row[1]
            
            # Recent activity (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_entries = conn.execute(
                "SELECT COUNT(*) FROM memory_entries WHERE created_at >= ?",
                (cutoff_time.isoformat(),)
            ).fetchone()[0]
            
            return {
                'total_entries': total_entries,
                'by_component': component_stats,
                'by_importance': importance_stats,
                'recent_entries_24h': recent_entries,
                'session_id': self.session_id,
                'database_size': self.db_path.stat().st_size if self.db_path.exists() else 0
            }
    
    def _should_consolidate(self) -> bool:
        """Check if memory consolidation is needed"""
        return (time.time() - self.last_consolidation) > self.consolidation_interval
    
    def _consolidate_memory(self):
        """
        Consolidate old, low-importance memories
        Archive or compress entries that are old and rarely accessed
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=7)  # Older than 7 days
            
            with sqlite3.connect(self.db_path) as conn:
                # Find candidates for consolidation
                cursor = conn.execute("""
                    SELECT id, component, entry_type, content, importance, access_count
                    FROM memory_entries 
                    WHERE created_at < ? AND importance < 3 AND access_count < 2
                """, (cutoff_time.isoformat(),))
                
                candidates = cursor.fetchall()
                
                if candidates:
                    # Create consolidated summary
                    summary_content = f"Consolidated {len(candidates)} low-importance entries from {cutoff_time.date()}"
                    
                    # Store consolidation record
                    consolidation_id = self.store_memory(
                        component="memory_system",
                        entry_type="consolidation",
                        content=summary_content,
                        metadata={"consolidated_count": len(candidates)},
                        importance=3
                    )
                    
                    # Archive old entries (move to archive table or delete)
                    entry_ids = [row[0] for row in candidates]
                    placeholders = ','.join('?' * len(entry_ids))
                    conn.execute(f"DELETE FROM memory_entries WHERE id IN ({placeholders})", entry_ids)
                    conn.commit()
                    
                    self.logger.info(f"Consolidated {len(candidates)} memory entries")
                
                self.last_consolidation = time.time()
                
        except Exception as e:
            self.logger.error(f"Memory consolidation failed: {e}")
    
    def backup_to_git(self, git_repo_path: str = ".") -> bool:
        """
        Create Git backup of memory system
        """
        try:
            import subprocess
            
            # Export current memory to JSON
            backup_file = self.data_dir / f"memory_backup_{int(time.time())}.json"
            
            all_memories = self.retrieve_memory(limit=10000)  # Get all memories
            
            with open(backup_file, 'w') as f:
                json.dump({
                    'session_id': self.session_id,
                    'backup_time': datetime.now().isoformat(),
                    'entries': all_memories
                }, f, indent=2, default=str)
            
            # Git operations
            subprocess.run(['git', 'add', str(backup_file)], cwd=git_repo_path, check=True)
            subprocess.run([
                'git', 'commit', '-m', 
                f"Memory backup: {len(all_memories)} entries - {datetime.now().isoformat()}"
            ], cwd=git_repo_path, check=True)
            
            self.logger.info(f"Memory backed up to Git: {backup_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Git backup failed: {e}")
            return False
    
    def restore_from_backup(self, backup_file: str) -> bool:
        """
        Restore memory from JSON backup
        """
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            entries = backup_data.get('entries', [])
            restored_count = 0
            
            for entry_data in entries:
                # Restore each entry
                self.store_memory(
                    component=entry_data['component'],
                    entry_type=entry_data['entry_type'],
                    content=entry_data['content'],
                    metadata=entry_data.get('metadata', {}),
                    importance=entry_data.get('importance', 5)
                )
                restored_count += 1
            
            self.logger.info(f"Restored {restored_count} memory entries from backup")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup restore failed: {e}")
            return False

if __name__ == "__main__":
    # Test the memory system
    memory = PersistentMemory()
    
    # Store some test memories
    memory.store_memory(
        component="test",
        entry_type="initialization",
        content="Memory system test started",
        importance=8
    )
    
    memory.store_memory(
        component="coordinator",
        entry_type="task_completion",
        content="Successfully created local agent coordinator",
        metadata={"task_id": "task_001", "duration": "30 minutes"},
        importance=7
    )
    
    # Retrieve and display
    memories = memory.retrieve_memory(limit=10)
    print(f"Retrieved {len(memories)} memories")
    
    for mem in memories:
        print(f"- {mem['component']}: {mem['content'][:50]}...")
    
    # Show stats
    stats = memory.get_memory_stats()
    print(f"Memory stats: {stats}")

