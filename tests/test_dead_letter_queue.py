import pytest
from app.services.dead_letter_queue import dlq

def test_push_to_dlq(sample_tenant):
    """Test pushing items to DLQ"""
    dlq_id = dlq.push(
        queue_name="test_queue",
        payload={"action": "test"},
        tenant_id=sample_tenant,
        error="Test error"
    )
    
    assert dlq_id > 0
    
    stats = dlq.get_tenant_stats(sample_tenant)
    assert "test_queue" in stats
    assert stats["test_queue"]["total"] == 1
    assert stats["test_queue"]["unresolved"] == 1

def test_mark_resolved(sample_tenant):
    """Test marking item as resolved"""
    dlq_id = dlq.push("test_queue", {"test": True}, sample_tenant)
    
    dlq.mark_resolved(dlq_id, {"resolution": "manual"})
    
    stats = dlq.get_tenant_stats(sample_tenant)
    assert stats["test_queue"]["resolved"] == 1
    assert stats["test_queue"]["unresolved"] == 0

def test_tenant_isolation_in_dlq():
    """Test DLQ items are isolated by tenant"""
    dlq.push("test_queue", {"a": 1}, "tenant_a")
    dlq.push("test_queue", {"b": 1}, "tenant_b")
    
    stats_a = dlq.get_tenant_stats("tenant_a")
    stats_b = dlq.get_tenant_stats("tenant_b")
    
    assert stats_a["test_queue"]["total"] == 1
    assert stats_b["test_queue"]["total"] == 1
