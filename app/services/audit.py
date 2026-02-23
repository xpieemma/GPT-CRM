from fastapi import HTTPException
from app.services.repository import repo
from app.utils.logging import logger
from app.config import settings

class AuditService:
    """
    Audit and compliance service with budget enforcement.
    
    Note: Budget check has a TOCTOU race condition in concurrent requests.
    In production, this would use Redis atomic operations.
    """
    
    def enforce_budget(self, tenant_id: str):
        """Enforce daily budget for tenant"""
        spent = repo.get_tenant_daily_cost(tenant_id)
        
        if spent >= settings.DEFAULT_DAILY_BUDGET:
            logger.warning(f"Budget exceeded for tenant {tenant_id}", extra={
                "spent": spent,
                "limit": settings.DEFAULT_DAILY_BUDGET
            })
            raise HTTPException(
                status_code=402,
                detail="Daily budget exceeded. Contact support to increase quota."
            )
        
        return {
            "tenant_id": tenant_id,
            "spent": spent,
            "remaining": settings.DEFAULT_DAILY_BUDGET - spent,
            "limit": settings.DEFAULT_DAILY_BUDGET
        }
    
    def log_interaction(self, tenant_id: str, lead_id: str, prompt_version: str,
                       model: str, context: dict, response: dict, cost: float):
        """Log interaction for audit trail"""
        metadata = {
            "prompt_version": prompt_version,
            "model_used": model,
            "cost_usd": cost,
            "audit_version": "1.0"
        }
        
        repo.log_conversation(
            tenant_id=tenant_id,
            lead_id=lead_id,
            messages={"context": context, "response": response},
            metadata=metadata
        )
        
        logger.info(f"Audit log created", extra={
            "tenant": tenant_id,
            "lead": lead_id,
            "cost": cost
        })

# Singleton
audit = AuditService()
