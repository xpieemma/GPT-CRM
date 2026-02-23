from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
from contextlib import asynccontextmanager

from app.api import webhooks, scheduler
from app.api.dependencies import rate_limit_dependency, get_tenant_id
from app.auth.oauth2 import oauth2_scheme
from app.config import settings
from app.utils.logging import logger, api_logger
from app.services.repository import repo
from app.services.dispatcher import dispatcher
from app.services.dead_letter_queue import dlq
from app.services.prompt_store import prompt_store
from app.services.metrics import metrics
from app.models import ConversationContext, Lead
from app.crm_client import crm_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.VERSION}")
    
    # Check database
    try:
        repo.get_active_prompt("default")
        logger.info("Database connected")
    except Exception as e:
        logger.error(f"Database error: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down")
    await crm_client.close()

# Create app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.ENVIRONMENT == "development" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    api_logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
    
    metrics.put_metric("ResponseTime", duration, "default", {"path": request.url.path})
    return response

# Error handler
@app.exception_handler(Exception)
async def global_exception(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Include routers
app.include_router(webhooks.router)
app.include_router(scheduler.router)

# Health check
@app.get("/health")
async def health():
    """Health check endpoint"""
    try:
        repo.get_active_prompt("default")
        db_status = "connected"
    except:
        db_status = "error"
    
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "timestamp": time.time()
    }

# Root
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": "/health"
    }

# Generate outreach endpoint
@app.post("/api/outreach/generate")
async def generate_outreach(
    lead_id: str,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_tenant_id),
    _=Depends(rate_limit_dependency),
    token: str = Depends(oauth2_scheme)
):
    """Generate outreach message for a lead"""
    
    # Get lead
    lead = await crm_client.get_lead(lead_id, tenant_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Create context
    context = ConversationContext(
        tenant_id=tenant_id,
        lead=lead,
        current_stage="initial_outreach"
    )
    
    # Dispatch to background task
    task_id = dispatcher.dispatch(
        "generate_outreach",
        {
            "context": context.dict(),
            "tenant_id": tenant_id
        },
        background_tasks
    )
    
    return {
        "status": "processing",
        "task_id": task_id,
        "tenant_id": tenant_id,
        "message": "Outreach generation started"
    }

# Task status endpoint
@app.get("/api/task/{task_id}")
async def get_task_status(
    task_id: str,
    tenant_id: str = Depends(get_tenant_id)
):
    """Get task status"""
    status = dispatcher.get_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status

# Tenant stats endpoint
@app.get("/api/tenant/stats")
async def get_tenant_stats(
    tenant_id: str = Depends(get_tenant_id)
):
    """Get tenant statistics"""
    return {
        "tenant_id": tenant_id,
        "daily_cost": repo.get_tenant_daily_cost(tenant_id),
        "dlq_stats": dlq.get_tenant_stats(tenant_id)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
