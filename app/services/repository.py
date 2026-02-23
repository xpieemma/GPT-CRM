import sqlite3
import json
import os
import gc
import time
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
from app.config import settings
from app.utils.logging import logger

class TenantAwareRepository:
    """
    Multi-tenant repository with explicit tenant_id parameters.
    
    All queries use parameterized inputs (? placeholders) and the tenant_id
    is always the last parameter, ensuring no SQL injection risk and proper
    data isolation.
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._init_db()
    
    def _init_db(self):
        """Ensure database exists with proper schema"""
        with self._get_connection() as conn:
            # Tables are created by migrations/init.sql
            pass
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with row factory"""
        from contextlib import closing

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            conn.close()
    
    # Prompt methods
    def get_active_prompt(self, tenant_id: str) -> Optional[Dict]:
        """Get active prompt for tenant"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM prompts 
                WHERE tenant_id = ? AND active = 1
                ORDER BY created_at DESC LIMIT 1
            """, (tenant_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_prompt(self, tenant_id: str, version: str, content: str, 
                     active: bool = False, metadata: Optional[Dict] = None) -> int:
        """Create new prompt for tenant"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO prompts (tenant_id, version, content, active, metadata)
                VALUES (?, ?, ?, ?, ?)
            """, (tenant_id, version, content, active, json.dumps(metadata or {})))
            return cursor.lastrowid
    
    # Metric methods
    def record_metric(self, tenant_id: str, name: str, value: float, 
                     dimensions: Optional[Dict] = None):
        """Record tenant-scoped metric"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO metrics (tenant_id, metric_name, value, dimensions)
                VALUES (?, ?, ?, ?)
            """, (tenant_id, name, value, json.dumps(dimensions or {})))
    
    def get_tenant_daily_cost(self, tenant_id: str) -> float:
        """Get today's total cost for tenant"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT COALESCE(SUM(value), 0) FROM metrics 
                WHERE tenant_id = ? 
                AND metric_name = 'TokenCost'
                AND timestamp >= datetime('now', 'start of day')
            """, (tenant_id,))
            return cursor.fetchone()[0]
    
    # Conversation methods
    def log_conversation(self, tenant_id: str, lead_id: str, 
                        messages: Dict, metadata: Dict):
        """Log conversation for audit trail"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO conversations (tenant_id, lead_id, messages, metadata)
                VALUES (?, ?, ?, ?)
            """, (tenant_id, lead_id, json.dumps(messages), json.dumps(metadata)))
    
    def get_conversations(self, tenant_id: str, lead_id: str, limit: int = 10) -> List[Dict]:
        """Get conversation history for lead"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM conversations 
                WHERE tenant_id = ? AND lead_id = ?
                ORDER BY created_at DESC LIMIT ?
            """, (tenant_id, lead_id, limit))
            return [dict(row) for row in cursor.fetchall()]
        

    def cleanup(self, force_delete: bool = False):
        """Clean up resources and optionally force database file deletion for testing"""
        import gc
        import time
        
        # Force garbage collection to close any lingering connections
        gc.collect()
        
        # Give the OS a moment to release file handles
        time.sleep(0.1)
        
        # For testing, we can try to delete the database file
        if force_delete and hasattr(self, 'db_path') and self.db_path != ":memory:":
            try:
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                    print(f"✅ Deleted test database: {self.db_path}")
            except PermissionError:
                print(f"⚠️  Could not delete {self.db_path} - might still be in use")
                # One more GC attempt
                gc.collect()
                time.sleep(0.2)
                try:
                  if os.path.exists(self.db_path):
                    os.remove(self.db_path)
                    print(f"✅ Deleted test database on second attempt: {self.db_path}")
                except:
                    pass  # Give up gracefully
                    print(f"⚠️  Final attempt failed to delete {self.db_path}")

# Singleton instance
repo = TenantAwareRepository()
