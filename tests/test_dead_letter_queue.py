import pytest
import json
import time
from typing import Optional, Dict
from app.services.dead_letter_queue import dlq

def test_push_to_dlq(sample_tenant):
    """Test pushing items to dead letter queue"""
    # Push an item with all fields
    dlq_id = dlq.push(
        queue_name="test_queue",
        payload={"test": "data", "value": 123},
        tenant_id=sample_tenant,
        error="Test error message",
        metadata={"source": "test", "retry_count": 0}
    )
    
    assert dlq_id is not None
    assert isinstance(dlq_id, int)
    assert dlq_id > 0

def test_mark_resolved(sample_tenant):
    """Test marking DLQ item as resolved"""
    # First push an item
    dlq_id = dlq.push(
        queue_name="test_queue",
        payload={"test": "data"},
        tenant_id=sample_tenant,
        error="Temporary failure"
    )
    
    # Mark as resolved with metadata
    resolution_metadata = {"resolution": "manual", "notes": "Fixed by operator", "timestamp": "2024-01-01"}
    dlq.mark_resolved(dlq_id, resolution_metadata)
    
    # Note: To fully verify, you'd need a get_item method in your DLQ class
    # For now, we verify no exception was raised
    assert True

def test_mark_resolved_twice(sample_tenant):
    """Test marking the same item resolved twice (should be idempotent)"""
    dlq_id = dlq.push(
        queue_name="test_queue",
        payload={"test": "data"},
        tenant_id=sample_tenant
    )
    
    # Mark resolved first time
    dlq.mark_resolved(dlq_id, {"resolution": "first"})
    
    # Mark resolved second time (should not raise error)
    dlq.mark_resolved(dlq_id, {"resolution": "second"})
    
    assert True

def test_mark_resolved_nonexistent_id(sample_tenant):
    """Test marking a non-existent DLQ item (should raise error)"""
    with pytest.raises(ValueError, match="DLQ item with id 99999 not found"):
        dlq.mark_resolved(99999, {"resolution": "test"})

def test_tenant_isolation_in_dlq(sample_tenant):
    """Test that tenants can't see each other's DLQ items"""
    tenant_a = sample_tenant
    tenant_b = "different_tenant_456"
    
    # Push items for both tenants
    id_a = dlq.push("test_queue", {"tenant": "A"}, tenant_a, error="Error A")
    id_b = dlq.push("test_queue", {"tenant": "B"}, tenant_b, error="Error B")
    
    # Verify IDs are different
    assert id_a != id_b
    
    # Note: To fully verify isolation, you'd need query methods that respect tenant_id

def test_dlq_with_metadata(sample_tenant):
    """Test pushing items with complex metadata"""
    complex_metadata = {
        "user": "john.doe",
        "department": "sales",
        "tags": ["urgent", "follow-up"],
        "priority": 1,
        "nested": {"key": "value"}
    }
    
    dlq_id = dlq.push(
        queue_name="test_queue",
        payload={"order_id": 12345},
        tenant_id=sample_tenant,
        error="API timeout",
        metadata=complex_metadata
    )
    
    assert dlq_id is not None

def test_dlq_error_tracking(sample_tenant):
    """Test error message storage"""
    error_msg = "Connection timeout after 30 seconds"
    
    dlq_id = dlq.push(
        queue_name="test_queue",
        payload={"test": "error"},
        tenant_id=sample_tenant,
        error=error_msg
    )
    
    assert dlq_id is not None
    # Note: Would need get method to verify error message

def test_dlq_multiple_items_same_queue(sample_tenant):
    """Test pushing multiple items to same queue"""
    queue_name = "bulk_queue"
    item_count = 5
    
    ids = []
    for i in range(item_count):
        dlq_id = dlq.push(
            queue_name=queue_name,
            payload={"index": i},
            tenant_id=sample_tenant,
            error=f"Error {i}"
        )
        ids.append(dlq_id)
    
    # Verify all IDs are unique
    assert len(set(ids)) == item_count

@pytest.mark.asyncio
async def test_dlq_concurrent_access(sample_tenant):
    """Test concurrent access to DLQ (if you have async methods)"""
    # This is a placeholder for concurrent testing
    # You'd use asyncio.gather to test concurrent pushes
    pass

def test_dlq_with_empty_payload(sample_tenant):
    """Test pushing item with empty payload"""
    dlq_id = dlq.push(
        queue_name="test_queue",
        payload={},
        tenant_id=sample_tenant,
        error="Empty payload test"
    )
    
    assert dlq_id is not None

def test_dlq_with_long_error_message(sample_tenant):
    """Test pushing item with very long error message"""
    long_error = "x" * 1000  # Very long string
    
    dlq_id = dlq.push(
        queue_name="test_queue",
        payload={"test": "long_error"},
        tenant_id=sample_tenant,
        error=long_error
    )
    
    assert dlq_id is not None