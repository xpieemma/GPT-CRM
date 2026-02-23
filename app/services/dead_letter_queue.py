import contextlib
import sqlite3
import json
from typing import Optional, Dict, Any, List
from app.config import settings
from app.utils.logging import logger

class DeadLetterQueue:
    """
    Persistent dead letter queue with tenant isolation.
    
    Uses Python-side JSON merging for cross-platform compatibility.
    """
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.DATABASE_PATH
    
    def push(self, queue_name: str, payload: Dict, tenant_id: str = "default",
             item_id: Optional[str] = None, error: Optional[str] = None,
             metadata: Optional[Dict] = None) -> int:
        """Push failed item to DLQ"""
        # Wrap in closing() to prevent Segmentation Faults on exit
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn: # Handles transaction commit/rollback
                cursor = conn.execute("""
                    INSERT INTO dead_letter_queue 
                    (queue_name, tenant_id, item_id, payload, error, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    queue_name,
                    tenant_id,
                    item_id,
                    json.dumps(payload),
                    error,
                    json.dumps(metadata) if metadata else None
                ))
                
                dlq_id = cursor.lastrowid
                
                logger.warning(f"Item added to DLQ", extra={
                    "dlq_id": dlq_id,
                    "queue": queue_name,
                    "tenant": tenant_id
                })
                
                return dlq_id
    
    def mark_resolved(self, dlq_id: int, metadata: Optional[Dict] = None):
        """
        Mark DLQ item as resolved.
        
        Raises ValueError if the item doesn't exist.
        """
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            with conn:
                # First check if the item exists
                cursor = conn.execute(
                    "SELECT id, metadata FROM dead_letter_queue WHERE id = ?", 
                    (dlq_id,)
                )
                row = cursor.fetchone()
                
                # Raise error if item doesn't exist
                if not row:
                    raise ValueError(f"DLQ item with id {dlq_id} not found")
                
                # Read current metadata
                current = json.loads(row[1]) if row[1] else {}
                
                # Merge in Python
                if metadata:
                    current.update(metadata)
                
                # Write back
                conn.execute("""
                    UPDATE dead_letter_queue 
                    SET resolved = 1, 
                        resolved_at = CURRENT_TIMESTAMP,
                        metadata = ?
                    WHERE id = ?
                """, (json.dumps(current), dlq_id))
                
                logger.info(f"DLQ item {dlq_id} resolved")
    
    def get_tenant_stats(self, tenant_id: str) -> Dict:
        """Get DLQ statistics for tenant"""
        with contextlib.closing(sqlite3.connect(self.db_path)) as conn:
            # We don't need 'with conn' here as we are only reading
            cursor = conn.execute("""
                SELECT 
                    queue_name,
                    COUNT(*) as total,
                    SUM(CASE WHEN resolved = 0 THEN 1 ELSE 0 END) as unresolved,
                    SUM(CASE WHEN resolved = 1 THEN 1 ELSE 0 END) as resolved,
                    AVG(retry_count) as avg_retries
                FROM dead_letter_queue
                WHERE tenant_id = ?
                GROUP BY queue_name
            """, (tenant_id,))
            
            stats = {}
            for row in cursor.fetchall():
                stats[row[0]] = {
                    "total": row[1],
                    "unresolved": row[2],
                    "resolved": row[3],
                    "avg_retries": round(row[4], 2) if row[4] else 0
                }
            return stats

# Singleton
dlq = DeadLetterQueue()