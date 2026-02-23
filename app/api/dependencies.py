from fastapi import Request, HTTPException, Depends
import time
from typing import Dict
from app.config import settings

class RateLimiter:
    """
    Rate limiter with configurable window for testing.
    
    In production: window=60 seconds
    In tests: window=1 second (for fast CI/CD)
    """
    
    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self._requests: Dict[str, list] = {}
    
    def check_rate_limit(self, key: str, limit: int) -> bool:
        """Check if request is within rate limit"""
        now = time.time()
        
        # Clean old requests
        if key in self._requests:
            self._requests[key] = [
                ts for ts in self._requests[key] 
                if now - ts < self.window
            ]
        else:
            self._requests[key] = []
        
        # Check limit
        if len(self._requests[key]) >= limit:
            return False
        
        # Add current request
        self._requests[key].append(now)
        return True
    
    def get_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests"""
        if key not in self._requests:
            return limit
        now = time.time()
        valid = [ts for ts in self._requests[key] if now - ts < self.window]
        return max(0, limit - len(valid))

# Create limiter with configured window
rate_limiter = RateLimiter(window_seconds=settings.RATE_LIMIT_WINDOW)

async def get_tenant_id(request: Request) -> str:
    """Extract tenant ID from header"""
    tenant_id = request.headers.get("X-Tenant-ID", "default")
    return tenant_id

async def rate_limit_dependency(
    request: Request,
    tenant_id: str = Depends(get_tenant_id)
):
    """Rate limiting dependency"""
    # Determine limit
    if request.headers.get("Authorization"):
        limit = settings.RATE_LIMIT_AUTHENTICATED
    else:
        limit = settings.RATE_LIMIT_ANONYMOUS
    
    if not rate_limiter.check_rate_limit(tenant_id, limit):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please slow down."
        )
    
    return {
        "tenant_id": tenant_id,
        "limit": limit,
        "remaining": rate_limiter.get_remaining(tenant_id, limit)
    }
