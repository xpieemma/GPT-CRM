# tests/conftest.py
import pytest
import sqlite3
import os
import time
import gc
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
from app.outreach_agent import outreach_agent  # Import the agent instance

# ... (keep all your existing fixtures like setup_test_db, sample_tenant, etc.)

@pytest.fixture
def mock_groq(monkeypatch):
    """Mock Groq client by replacing the instantiated client directly."""
    
    # 1. Create the shape of the mock response
    class MockMessage:
        def __init__(self, content):
            self.content = content
    
    class MockChoice:
        def __init__(self, message):
            self.message = message
    
    class MockCompletion:
        def __init__(self):
            # The agent expects a JSON string with these keys based on your previous logs
            self.choices = [MockChoice(MockMessage('{"message": "Hello from mock", "confidence_score": 0.9}'))]
            self.usage = MagicMock(prompt_tokens=10, completion_tokens=5)
    
    # 2. Setup the fake client
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=MockCompletion())
    
    # 3. Swap the live client with the fake client safely
    # Save original for cleanup if needed
    original_client = getattr(outreach_agent, "client", None)
    monkeypatch.setattr(outreach_agent, "client", mock_client)
    
    yield mock_client
    
    # Optional: restore original if needed for other tests
    if original_client:
        monkeypatch.setattr(outreach_agent, "client", original_client)