import pytest
from fastapi import HTTPException
from app.services.audit import audit
from app.services.repository import repo

def test_budget_enforcement_within_limit(sample_tenant):
    """Test budget check when under limit"""
    repo.record_metric(sample_tenant, "TokenCost", 1.00)
    
    result = audit.enforce_budget(sample_tenant)
    assert result["remaining"] > 0

def test_budget_enforcement_exceeds_limit(sample_tenant):
    """Test budget check when over limit"""
    from app.config import settings
    repo.record_metric(sample_tenant, "TokenCost", settings.DEFAULT_DAILY_BUDGET + 1.00)
    
    with pytest.raises(HTTPException) as exc:
        audit.enforce_budget(sample_tenant)
    assert exc.value.status_code == 402

def test_audit_log_creation(sample_tenant):
    """Test audit log creation"""
    audit.log_interaction(
        tenant_id=sample_tenant,
        lead_id="lead_123",
        prompt_version="v1",
        model="llama3-8b-8192",
        context={"test": "context"},
        response={"message": "hello"},
        cost=0.05
    )
    
    convs = repo.get_conversations(sample_tenant, "lead_123")
    assert len(convs) == 1
    assert "cost_usd" in convs[0]["metadata"]
