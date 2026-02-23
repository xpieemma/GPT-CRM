from typing import Optional
from app.models import Lead, LeadStatus
from app.utils.logging import logger

class CRMClient:
    """Mock CRM client for demo"""
    
    async def get_lead(self, lead_id: str, tenant_id: str = "default") -> Optional[Lead]:
        """Get lead from CRM"""
        # Mock implementation
        if lead_id == "test_123":
            return Lead(
                id="test_123",
                first_name="John",
                last_name="Doe",
                email="john@example.com",
                company="Acme Inc",
                position="CTO",
                status=LeadStatus.NEW,
                score=85
            )
        return None
    
    async def update_lead_status(self, lead_id: str, status: str, notes: str = ""):
        """Update lead status"""
        logger.info(f"Updated lead {lead_id} to {status}")
    
    async def close(self):
        """Cleanup"""
        pass

# Singleton
crm_client = CRMClient()
