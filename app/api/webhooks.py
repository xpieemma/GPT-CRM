from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException
import hmac
import hashlib
from app.config import settings
from app.models import WebhookEvent
from app.utils.logging import webhook_logger
from app.api.dependencies import rate_limit_dependency, get_tenant_id
from app.services.dead_letter_queue import dlq

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

async def verify_signature(request: Request, signature: str):
    """Verify webhook signature"""
    body = await request.body()
    expected = hmac.new(
        settings.WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(signature, expected):
        raise HTTPException(status_code=401, detail="Invalid signature")

@router.post("/crm-update")
async def crm_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_tenant_id),
    _=Depends(rate_limit_dependency),
    x_webhook_signature: str = None
):
    """Handle CRM webhooks"""
    # Verify signature
    if x_webhook_signature:
        await verify_signature(request, x_webhook_signature)
    
    # Parse payload
    try:
        payload = await request.json()
        event = WebhookEvent(**payload)
        
        webhook_logger.info(f"Webhook received", extra={
            "tenant": tenant_id,
            "type": event.event_type,
            "lead": event.lead_id
        })
        
        # Process in background
        background_tasks.add_task(process_webhook, event, tenant_id)
        
        return {"status": "received", "event_id": event.lead_id}
        
    except Exception as e:
        # Push to DLQ on failure
        dlq.push(
            queue_name="webhook_failures",
            payload=payload if 'payload' in locals() else {},
            tenant_id=tenant_id,
            error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

async def process_webhook(event: WebhookEvent, tenant_id: str):
    """Process webhook in background"""
    webhook_logger.info(f"Processing webhook for lead {event.lead_id}")
    # Actual processing logic here
