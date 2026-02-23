import pytest
import sqlite3
import os
from typing import Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

# Set test environment
os.environ["ENVIRONMENT"] = "test"
os.environ["RATE_LIMIT_WINDOW"] = "1"  # Fast tests!
os.environ["DATABASE_PATH"] = "data/test.db"
os.environ["GROQ_API_KEY"] = "test-key"
os.environ["WEBHOOK_SECRET"] = "test-secret"
os.environ["JWT_SECRET_KEY"] = "test-jwt"

from app.config import settings
from app.services.repository import repo
from app.services.dead_letter_queue import dlq
from app.api.dependencies import RateLimiter

@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database"""
    # Ensure clean test db
    if os.path.exists("data/test.db"):
        os.remove("data/test.db")
    
    # Create tables
    with sqlite3.connect("data/test.db") as conn:
        conn.execute("""
            CREATE TABLE prompts (
                id INTEGER PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                version TEXT NOT NULL,
                content TEXT NOT NULL,
                active BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE metrics (
                id INTEGER PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL,
                dimensions TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE conversations (
                id INTEGER PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                lead_id TEXT NOT NULL,
                messages TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE dead_letter_queue (
                id INTEGER PRIMARY KEY,
                tenant_id TEXT NOT NULL,
                queue_name TEXT NOT NULL,
                item_id TEXT,
                payload TEXT NOT NULL,
                error TEXT,
                failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retry_count INTEGER DEFAULT 0,
                resolved BOOLEAN DEFAULT 0,
                metadata TEXT
            )
        """)
    
    yield
    
    # Cleanup
    if os.path.exists("data/test.db"):
        os.remove("data/test.db")

@pytest.fixture
def sample_tenant():
    return "test_tenant_123"

@pytest.fixture
def rate_limiter():
    return RateLimiter(window_seconds=1)  # Fast tests

@pytest.fixture
def mock_groq():
    with patch('groq.AsyncGroq') as mock:
        client = AsyncMock()
        completion = AsyncMock()
        completion.choices = [MagicMock(message=MagicMock(content='{"message": "test", "confidence_score": 0.9}'))]
        completion.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
        client.chat.completions.create = AsyncMock(return_value=completion)
        mock.return_value = client
        yield mock
