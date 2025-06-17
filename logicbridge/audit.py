"""
Audit logging and rule versioning module
"""

import os
import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .core import Decision


@dataclass
class AuditEntry:
    """Audit log entry"""
    id: int
    rule_sha: str
    author: str
    timestamp: str
    prompt_sha: Optional[str]
    llm_model: Optional[str]
    diff_url: Optional[str]
    content: str


class AuditLogger:
    """Handles audit logging and rule versioning"""
    
    def __init__(self, db_path: str = "logicbridge_audit.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the audit database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rule_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_sha TEXT NOT NULL,
                    author TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    prompt_sha TEXT,
                    llm_model TEXT,
                    diff_url TEXT,
                    content TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL,
                    rule_sha TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    elapsed_us INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    payload_hash TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rule_changes_sha ON rule_changes(rule_sha)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rule_changes_timestamp ON rule_changes(timestamp)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_decisions_timestamp ON decisions(timestamp)
            """)
    
    def log_ruleset_change(
        self, 
        rule_sha: str, 
        author: str, 
        content: str,
        prompt_sha: Optional[str] = None,
        llm_model: Optional[str] = None,
        diff_url: Optional[str] = None
    ):
        """Log a ruleset change"""
        timestamp = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO rule_changes 
                (rule_sha, author, timestamp, prompt_sha, llm_model, diff_url, content)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (rule_sha, author, timestamp, prompt_sha, llm_model, diff_url, content))
    
    def log_decision(self, decision: Decision, payload: Optional[Dict[str, Any]] = None):
        """Log a rule decision"""
        # Hash payload for privacy
        payload_hash = "unknown"
        if payload:
            payload_str = json.dumps(payload, sort_keys=True)
            payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()[:16]
        
        timestamp = datetime.utcfromtimestamp(decision.timestamp).isoformat()
        outcome_json = json.dumps(decision.outcome)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO decisions 
                (rule_id, rule_sha, outcome, elapsed_us, timestamp, payload_hash)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                decision.rule_id,
                decision.rule_sha,
                outcome_json,
                decision.elapsed_us,
                timestamp,
                payload_hash
            ))
    
    def get_log_entries(self, limit: int = 100, since: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get audit log entries"""
        query = "SELECT * FROM rule_changes ORDER BY timestamp DESC LIMIT ?"
        params = [limit]
        
        if since:
            # Parse since parameter (e.g., "7d", "30d")
            if since.endswith('d'):
                days = int(since[:-1])
                since_date = datetime.utcnow() - timedelta(days=days)
                query = "SELECT * FROM rule_changes WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT ?"
                params = [since_date.isoformat(), limit]
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            
            entries = []
            for row in cursor:
                entries.append({
                    "id": row["id"],
                    "rule_sha": row["rule_sha"],
                    "author": row["author"],
                    "timestamp": row["timestamp"],
                    "prompt_sha": row["prompt_sha"],
                    "llm_model": row["llm_model"],
                    "diff_url": row["diff_url"]
                })
            
            return entries
    
    def get_latest_change_timestamp(self) -> Optional[str]:
        """Get timestamp of latest rule change"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT timestamp FROM rule_changes ORDER BY timestamp DESC LIMIT 1"
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_rule_content(self, rule_sha: str) -> Optional[str]:
        """Get rule content by SHA"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT content FROM rule_changes WHERE rule_sha = ? LIMIT 1",
                (rule_sha,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    
    def get_rule_diff(self, rule_sha1: str, rule_sha2: str) -> Optional[str]:
        """Get diff between two rule versions"""
        content1 = self.get_rule_content(rule_sha1)
        content2 = self.get_rule_content(rule_sha2)
        
        if not content1 or not content2:
            return None
        
        # Simple diff implementation
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        diff_lines = []
        diff_lines.append(f"--- {rule_sha1}")
        diff_lines.append(f"+++ {rule_sha2}")
        
        # Very basic line-by-line diff
        max_lines = max(len(lines1), len(lines2))
        for i in range(max_lines):
            line1 = lines1[i] if i < len(lines1) else ""
            line2 = lines2[i] if i < len(lines2) else ""
            
            if line1 != line2:
                if line1:
                    diff_lines.append(f"- {line1}")
                if line2:
                    diff_lines.append(f"+ {line2}")
        
        return "\n".join(diff_lines)
    
    def get_decision_stats(self, since_hours: int = 24) -> Dict[str, Any]:
        """Get decision statistics"""
        since_timestamp = datetime.utcnow() - timedelta(hours=since_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total_decisions,
                    AVG(elapsed_us) as avg_elapsed_us,
                    MAX(elapsed_us) as max_elapsed_us,
                    COUNT(DISTINCT rule_id) as unique_rules_triggered
                FROM decisions 
                WHERE timestamp >= ?
            """, (since_timestamp.isoformat(),))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    "total_decisions": row[0],
                    "avg_elapsed_us": round(row[1], 2) if row[1] else 0,
                    "max_elapsed_us": row[2] or 0,
                    "unique_rules_triggered": row[3]
                }
            else:
                return {
                    "total_decisions": 0,
                    "avg_elapsed_us": 0,
                    "max_elapsed_us": 0,
                    "unique_rules_triggered": 0
                }
