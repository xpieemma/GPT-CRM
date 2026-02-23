import pytest
from app.services.repository import repo

def test_get_active_prompt_empty(sample_tenant):
    """Test getting prompt when none exists"""
    prompt = repo.get_active_prompt(sample_tenant)
    assert prompt is None

def test_create_and_get_prompt(sample_tenant):
    """Test creating and retrieving prompt"""
    repo.create_prompt(
        tenant_id=sample_tenant,
        version="v1",
        content="Test prompt",
        active=True
    )
    
    prompt = repo.get_active_prompt(sample_tenant)
    assert prompt is not None
    assert prompt["version"] == "v1"
    assert prompt["content"] == "Test prompt"

def test_tenant_isolation(sample_tenant):
    """Test prompts are isolated by tenant"""
    repo.create_prompt("tenant_a", "v1", "Content A", active=True)
    repo.create_prompt("tenant_b", "v1", "Content B", active=True)
    
    assert repo.get_active_prompt("tenant_a")["content"] == "Content A"
    assert repo.get_active_prompt("tenant_b")["content"] == "Content B"

def test_daily_cost_calculation(sample_tenant):
    """Test daily cost aggregation"""
    repo.record_metric(sample_tenant, "TokenCost", 0.5)
    repo.record_metric(sample_tenant, "TokenCost", 0.3)
    repo.record_metric("other_tenant", "TokenCost", 10.0)  # Different tenant
    
    cost = repo.get_tenant_daily_cost(sample_tenant)
    assert cost == 0.8  # 0.5 + 0.3
