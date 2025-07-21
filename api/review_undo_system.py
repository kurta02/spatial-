#!/usr/bin/env python3
"""
Review/Undo System - User approval and rollback capabilities for all agent decisions
Implements the missing piece: user control over AI actions
"""

import json
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
from pathlib import Path

class ActionType(Enum):
    MEMORY_STORE = "memory_store"
    MEMORY_CONSOLIDATE = "memory_consolidate"
    MEMORY_DELETE = "memory_delete"
    FILE_OPERATION = "file_operation"
    SYSTEM_CHANGE = "system_change"
    COMPONENT_START = "component_start"
    COMPONENT_STOP = "component_stop"

class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"

@dataclass
class PendingAction:
    id: str
    action_type: ActionType
    description: str
    details: Dict[str, Any]
    original_data: Dict[str, Any]  # For rollback
    timestamp: datetime
    approval_status: ApprovalStatus
    reasoning: str
    risk_level: str  # low, medium, high
    auto_approve: bool = False
    expires_at: Optional[datetime] = None

@dataclass
class UndoEntry:
    id: str
    action_id: str
    action_type: ActionType
    description: str
    rollback_data: Dict[str, Any]
    timestamp: datetime
    can_undo: bool = True

class ReviewUndoSystem:
    """
    System for user approval and undo capabilities
    No AI action occurs without user consent
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or "/home/kurt/migration-workspace/review_undo.db"
        self.pending_actions: Dict[str, PendingAction] = {}
        self.undo_stack: List[UndoEntry] = []
        self.max_undo_entries = 50
        self.auto_approve_low_risk = False  # User must enable this
        self.lock = threading.Lock()
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize database
        self._init_database()
        self._load_pending_actions()
        
        self.logger.info("Review/Undo System initialized")
    
    def _init_database(self):
        """Initialize SQLite database for persistence"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS pending_actions (
                    id TEXT PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    details TEXT NOT NULL,
                    original_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    approval_status TEXT NOT NULL,
                    reasoning TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    auto_approve INTEGER NOT NULL,
                    expires_at TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS undo_entries (
                    id TEXT PRIMARY KEY,
                    action_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    rollback_data TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    can_undo INTEGER NOT NULL
                )
            """)
            
            conn.commit()
    
    def _load_pending_actions(self):
        """Load pending actions from database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM pending_actions WHERE approval_status = 'pending'")
            for row in cursor.fetchall():
                action = PendingAction(
                    id=row[0],
                    action_type=ActionType(row[1]),
                    description=row[2],
                    details=json.loads(row[3]),
                    original_data=json.loads(row[4]),
                    timestamp=datetime.fromisoformat(row[5]),
                    approval_status=ApprovalStatus(row[6]),
                    reasoning=row[7],
                    risk_level=row[8],
                    auto_approve=bool(row[9]),
                    expires_at=datetime.fromisoformat(row[10]) if row[10] else None
                )
                self.pending_actions[action.id] = action
    
    def _save_pending_action(self, action: PendingAction):
        """Save pending action to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO pending_actions 
                (id, action_type, description, details, original_data, timestamp, 
                 approval_status, reasoning, risk_level, auto_approve, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                action.id, action.action_type.value, action.description,
                json.dumps(action.details), json.dumps(action.original_data),
                action.timestamp.isoformat(), action.approval_status.value,
                action.reasoning, action.risk_level, int(action.auto_approve),
                action.expires_at.isoformat() if action.expires_at else None
            ))
            conn.commit()
    
    def _save_undo_entry(self, entry: UndoEntry):
        """Save undo entry to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO undo_entries 
                (id, action_id, action_type, description, rollback_data, timestamp, can_undo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.id, entry.action_id, entry.action_type.value,
                entry.description, json.dumps(entry.rollback_data),
                entry.timestamp.isoformat(), int(entry.can_undo)
            ))
            conn.commit()
    
    def request_approval(self, 
                        action_type: ActionType,
                        description: str,
                        details: Dict[str, Any],
                        original_data: Dict[str, Any],
                        reasoning: str,
                        risk_level: str = "medium",
                        auto_approve: bool = False,
                        expires_in_minutes: int = 60) -> str:
        """
        Request user approval for an action
        Returns action ID for tracking
        """
        with self.lock:
            action_id = str(uuid.uuid4())
            expires_at = datetime.now() + timedelta(minutes=expires_in_minutes)
            
            action = PendingAction(
                id=action_id,
                action_type=action_type,
                description=description,
                details=details,
                original_data=original_data,
                timestamp=datetime.now(),
                approval_status=ApprovalStatus.PENDING,
                reasoning=reasoning,
                risk_level=risk_level,
                auto_approve=auto_approve,
                expires_at=expires_at
            )
            
            # Check for auto-approval
            if auto_approve and self.auto_approve_low_risk and risk_level == "low":
                action.approval_status = ApprovalStatus.AUTO_APPROVED
                self.logger.info(f"Auto-approved low-risk action: {action_id}")
            
            self.pending_actions[action_id] = action
            self._save_pending_action(action)
            
            self.logger.info(f"Approval requested: {action_type.value} - {description}")
            return action_id
    
    def approve_action(self, action_id: str, user_note: str = "") -> bool:
        """Approve a pending action"""
        with self.lock:
            if action_id not in self.pending_actions:
                self.logger.error(f"Action not found: {action_id}")
                return False
            
            action = self.pending_actions[action_id]
            action.approval_status = ApprovalStatus.APPROVED
            
            # Save approval
            self._save_pending_action(action)
            
            self.logger.info(f"Action approved: {action_id} - {action.description}")
            if user_note:
                self.logger.info(f"User note: {user_note}")
            
            return True
    
    def reject_action(self, action_id: str, reason: str = "") -> bool:
        """Reject a pending action"""
        with self.lock:
            if action_id not in self.pending_actions:
                self.logger.error(f"Action not found: {action_id}")
                return False
            
            action = self.pending_actions[action_id]
            action.approval_status = ApprovalStatus.REJECTED
            
            # Save rejection
            self._save_pending_action(action)
            
            self.logger.info(f"Action rejected: {action_id} - {action.description}")
            if reason:
                self.logger.info(f"Rejection reason: {reason}")
            
            # Remove from pending
            del self.pending_actions[action_id]
            return True
    
    def is_approved(self, action_id: str) -> bool:
        """Check if action is approved"""
        if action_id not in self.pending_actions:
            return False
        
        action = self.pending_actions[action_id]
        return action.approval_status in [ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED]
    
    def mark_executed(self, action_id: str, rollback_data: Dict[str, Any] = None):
        """Mark action as executed and add to undo stack"""
        with self.lock:
            if action_id not in self.pending_actions:
                self.logger.error(f"Action not found for execution: {action_id}")
                return
            
            action = self.pending_actions[action_id]
            
            # Add to undo stack if rollback data provided
            if rollback_data:
                undo_entry = UndoEntry(
                    id=str(uuid.uuid4()),
                    action_id=action_id,
                    action_type=action.action_type,
                    description=f"Undo: {action.description}",
                    rollback_data=rollback_data,
                    timestamp=datetime.now(),
                    can_undo=True
                )
                
                self.undo_stack.append(undo_entry)
                self._save_undo_entry(undo_entry)
                
                # Maintain stack size
                while len(self.undo_stack) > self.max_undo_entries:
                    removed = self.undo_stack.pop(0)
                    self.logger.debug(f"Removed old undo entry: {removed.id}")
            
            # Remove from pending
            del self.pending_actions[action_id]
            
            self.logger.info(f"Action executed: {action_id} - {action.description}")
    
    def get_pending_actions(self) -> List[PendingAction]:
        """Get all pending actions"""
        with self.lock:
            # Clean up expired actions
            now = datetime.now()
            expired_ids = []
            for action_id, action in self.pending_actions.items():
                if action.expires_at and action.expires_at < now:
                    expired_ids.append(action_id)
            
            for action_id in expired_ids:
                self.logger.info(f"Action expired: {action_id}")
                del self.pending_actions[action_id]
            
            return list(self.pending_actions.values())
    
    def get_undo_stack(self, limit: int = 10) -> List[UndoEntry]:
        """Get recent undo entries"""
        return self.undo_stack[-limit:] if limit else self.undo_stack
    
    def undo_action(self, undo_id: str) -> Dict[str, Any]:
        """Undo a previous action"""
        with self.lock:
            undo_entry = None
            for entry in self.undo_stack:
                if entry.id == undo_id:
                    undo_entry = entry
                    break
            
            if not undo_entry:
                raise ValueError(f"Undo entry not found: {undo_id}")
            
            if not undo_entry.can_undo:
                raise ValueError(f"Action cannot be undone: {undo_id}")
            
            # Mark as undone
            undo_entry.can_undo = False
            
            self.logger.info(f"Action undone: {undo_id} - {undo_entry.description}")
            return undo_entry.rollback_data
    
    def get_approval_summary(self) -> Dict[str, Any]:
        """Get summary of approval system status"""
        with self.lock:
            pending = len(self.pending_actions)
            undo_available = len([e for e in self.undo_stack if e.can_undo])
            
            risk_counts = {}
            for action in self.pending_actions.values():
                risk_counts[action.risk_level] = risk_counts.get(action.risk_level, 0) + 1
            
            return {
                "pending_actions": pending,
                "undo_entries_available": undo_available,
                "total_undo_entries": len(self.undo_stack),
                "auto_approve_enabled": self.auto_approve_low_risk,
                "risk_breakdown": risk_counts,
                "system_status": "active"
            }
    
    def clear_old_entries(self, days_old: int = 30):
        """Clear old entries from database"""
        cutoff = datetime.now() - timedelta(days=days_old)
        
        with sqlite3.connect(self.db_path) as conn:
            # Clear old undo entries
            conn.execute("DELETE FROM undo_entries WHERE timestamp < ?", (cutoff.isoformat(),))
            
            # Clear old approved/rejected actions
            conn.execute("""
                DELETE FROM pending_actions 
                WHERE approval_status IN ('approved', 'rejected') 
                AND timestamp < ?
            """, (cutoff.isoformat(),))
            
            conn.commit()
        
        self.logger.info(f"Cleared entries older than {days_old} days")

def demo_review_undo_system():
    """Demonstrate the review/undo system"""
    print("🔍 Review/Undo System Demo")
    print("=" * 40)
    
    # Initialize system
    review_system = ReviewUndoSystem()
    
    # Test 1: Request approval for memory operation
    print("\n1. Requesting approval for memory consolidation...")
    action_id = review_system.request_approval(
        action_type=ActionType.MEMORY_CONSOLIDATE,
        description="Consolidate memory entries older than 7 days",
        details={"entries_count": 15, "age_threshold": "7 days"},
        original_data={"before_consolidation": "data snapshot"},
        reasoning="Reduce memory database size for better performance",
        risk_level="medium"
    )
    print(f"   Action ID: {action_id}")
    
    # Test 2: Check pending actions
    print("\n2. Checking pending actions...")
    pending = review_system.get_pending_actions()
    print(f"   Pending actions: {len(pending)}")
    for action in pending:
        print(f"   - {action.action_type.value}: {action.description}")
        print(f"     Risk: {action.risk_level}, Status: {action.approval_status.value}")
    
    # Test 3: Approve action
    print("\n3. Approving action...")
    approved = review_system.approve_action(action_id, "Looks good, proceed")
    print(f"   Approved: {approved}")
    print(f"   Is approved: {review_system.is_approved(action_id)}")
    
    # Test 4: Mark as executed with undo data
    print("\n4. Marking as executed...")
    review_system.mark_executed(action_id, {
        "action": "restore_consolidated_entries",
        "backup_file": "/tmp/memory_backup_123.json",
        "entry_count": 15
    })
    
    # Test 5: Check undo stack
    print("\n5. Checking undo stack...")
    undo_stack = review_system.get_undo_stack()
    print(f"   Available undo operations: {len(undo_stack)}")
    for entry in undo_stack:
        print(f"   - {entry.description} (can undo: {entry.can_undo})")
    
    # Test 6: Get system summary
    print("\n6. System summary...")
    summary = review_system.get_approval_summary()
    print(f"   Pending: {summary['pending_actions']}")
    print(f"   Undo available: {summary['undo_entries_available']}")
    print(f"   Auto-approve: {summary['auto_approve_enabled']}")
    print(f"   Status: {summary['system_status']}")
    
    print("\n✅ Review/Undo System demo complete!")
    return review_system

if __name__ == "__main__":
    demo_review_undo_system()