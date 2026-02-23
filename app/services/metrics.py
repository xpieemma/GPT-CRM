from app.services.repository import repo
from typing import Optional, Dict

class MetricsCollector:
    """Simple metrics collection"""
    
    def put_metric(self, name: str, value: float, tenant_id: str = "default",
                  dimensions: Optional[Dict] = None):
        """Record a metric"""
        repo.record_metric(tenant_id, name, value, dimensions)
    
    def increment(self, name: str, tenant_id: str = "default",
                 dimensions: Optional[Dict] = None):
        """Increment a counter"""
        self.put_metric(name, 1, tenant_id, dimensions)

# Singleton
metrics = MetricsCollector()
