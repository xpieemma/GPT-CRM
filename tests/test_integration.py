from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "version" in data

def test_generate_outreach_without_auth():
    """Test outreach generation without auth"""
    response = client.post(
        "/api/outreach/generate?lead_id=test_123",
        headers={"X-Tenant-ID": "test_tenant"}
    )
    assert response.status_code in [200, 202]

def test_tenant_stats():
    """Test tenant stats endpoint"""
    response = client.get(
        "/api/tenant/stats",
        headers={"X-Tenant-ID": "test_tenant"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "tenant_id" in data
    assert "daily_cost" in data
