from fastapi import APIRouter, Depends
from app.api.dependencies import rate_limit_dependency, get_tenant_id
from app.utils.logging import logger

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

@router.post("/meeting")
async def schedule_meeting(
    lead_id: str,
    meeting_time: str,
    tenant_id: str = Depends(get_tenant_id),
    _=Depends(rate_limit_dependency)
):
    """Schedule a meeting"""
    logger.info(f"Meeting scheduled", extra={
        "tenant": tenant_id,
        "lead": lead_id,
        "time": meeting_time
    })
    return {"status": "scheduled", "lead_id": lead_id, "time": meeting_time}
