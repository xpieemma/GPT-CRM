import pytest
from fastapi import BackgroundTasks
from unittest.mock import AsyncMock, patch
from app.services.dispatcher import dispatcher

@pytest.mark.asyncio
async def test_dispatch_task(sample_tenant):
    """Test task dispatching"""
    background_tasks = BackgroundTasks()
    
    task_id = dispatcher.dispatch(
        "generate_outreach",
        {
            "context": {"lead": {"id": "123"}, "tenant_id": sample_tenant},
            "tenant_id": sample_tenant
        },
        background_tasks
    )
    
    assert task_id is not None
    assert len(background_tasks.tasks) == 1
    
    status = dispatcher.get_status(task_id)
    assert status["status"] == "pending"

def test_unknown_task_type(sample_tenant):
    """Test unknown task type handling"""
    background_tasks = BackgroundTasks()
    
    task_id = dispatcher.dispatch(
        "unknown_type",
        {},
        background_tasks
    )
    
    status = dispatcher.get_status(task_id)
    assert status["status"] == "failed"
    assert "Unknown" in status["error"]

def test_nonexistent_task():
    """Test getting status for nonexistent task"""
    status = dispatcher.get_status("fake-id")
    assert status is None
