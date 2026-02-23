# tests/test_agent.py
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.outreach_agent import outreach_agent
from app.models import ConversationContext, Lead, LeadStatus

@pytest.mark.asyncio
async def test_generate_response_basic(sample_tenant, mock_groq):
    """Test basic response generation"""
    lead = Lead(
        id="123",
        first_name="John",
        last_name="Doe",
        email="john@test.com",
        company="TestCo",
        position="Engineer",
        status=LeadStatus.NEW
    )
    
    context = ConversationContext(
        tenant_id=sample_tenant,
        lead=lead
    )
    
    with patch('app.services.audit.audit.enforce_budget') as mock_budget, \
         patch('app.services.prompt_store.prompt_store.get_active_prompt') as mock_prompt:
        
        mock_budget.return_value = {"remaining": 5.0}
        mock_prompt.return_value = {"version": "v1", "content": "test"}
        
        # The mock_groq fixture already provides a properly configured mock
        response = await outreach_agent.generate_response(context, tenant_id=sample_tenant)
        
        assert response is not None
        assert response.schema_version == "1.0"
        
        # Verify the mock was called
        mock_groq.return_value.chat.completions.create.assert_called_once()

@pytest.mark.asyncio
async def test_fallback_on_parse_failure(sample_tenant, mock_groq):
    """Test fallback when JSON parsing fails"""
    # Override the mock for this specific test
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock(message=MagicMock(content="not json"))]
    mock_completion.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
    
    mock_groq.return_value.chat.completions.create = AsyncMock(return_value=mock_completion)
    
    lead = Lead(
        id="123",
        first_name="John",
        last_name="Doe",
        email="john@test.com",
        company="TestCo",
        position="Engineer",
        status=LeadStatus.NEW
    )
    
    context = ConversationContext(
        tenant_id=sample_tenant,
        lead=lead
    )
    
    with patch('app.services.audit.audit.enforce_budget') as mock_budget, \
         patch('app.services.prompt_store.prompt_store.get_active_prompt') as mock_prompt:
        
        mock_budget.return_value = {"remaining": 5.0}
        mock_prompt.return_value = {"version": "v1", "content": "test"}
        
        response = await outreach_agent.generate_response(context, tenant_id=sample_tenant)
        
        assert response.requires_human is True
        assert response.confidence_score == 0.0