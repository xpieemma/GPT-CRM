import pytest
import time
from app.api.dependencies import RateLimiter

class TestRateLimiter:
    
    def test_basic_rate_limit(self):
        """Test basic rate limiting with 1-second window"""
        limiter = RateLimiter(window_seconds=1)
        key = "test_user"
        limit = 3
        
        for i in range(3):
            assert limiter.check_rate_limit(key, limit) is True
        
        assert limiter.check_rate_limit(key, limit) is False
    
    def test_rate_limit_reset(self):
        """Test rate limit resets after window"""
        limiter = RateLimiter(window_seconds=1)
        key = "reset_test"
        limit = 2
        
        assert limiter.check_rate_limit(key, limit) is True
        assert limiter.check_rate_limit(key, limit) is True
        assert limiter.check_rate_limit(key, limit) is False
        
        time.sleep(1.1)
        
        assert limiter.check_rate_limit(key, limit) is True
    
    def test_tenant_isolation(self):
        """Test different tenants have independent limits"""
        limiter = RateLimiter(window_seconds=1)
        tenant_a = "tenant_a"
        tenant_b = "tenant_b"
        limit = 2
        
        assert limiter.check_rate_limit(tenant_a, limit) is True
        assert limiter.check_rate_limit(tenant_a, limit) is True
        assert limiter.check_rate_limit(tenant_a, limit) is False
        
        assert limiter.check_rate_limit(tenant_b, limit) is True
    
    def test_get_remaining(self):
        """Test getting remaining requests"""
        limiter = RateLimiter(window_seconds=1)
        key = "remaining_test"
        limit = 5
        
        assert limiter.get_remaining(key, limit) == 5
        
        for i in range(3):
            limiter.check_rate_limit(key, limit)
        
        assert limiter.get_remaining(key, limit) == 2
