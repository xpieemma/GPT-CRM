import pytest
import sqlite3
import os
import time
import gc
import uuid
import json
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
from app.outreach_agent import outreach_agent

# Keep track of created fallback files for final cleanup
_fallback_files = []

@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database with proper cleanup and unique file fallback"""
    base_db_path = "data/test.db"
    os.makedirs("data", exist_ok=True)

    # 1. Close any existing connections
    repo.cleanup()
    gc.collect()

    actual_db_path = base_db_path

    # 2. Try to remove the old test DB, fall back to unique file if locked
    if os.path.exists(base_db_path):
        for attempt in range(3):
            try:
                os.remove(base_db_path)
                print(f"✅ Removed existing test database (attempt {attempt + 1})")
                break
            except PermissionError:
                if attempt < 2:
                    print(f"⚠️  Database locked, retrying... (attempt {attempt + 1})")
                    repo.cleanup()
                    gc.collect()
                    time.sleep(0.2)
                else:
                    # Fall back to a unique file instead of :memory:
                    unique_id = uuid.uuid4().hex[:8]
                    actual_db_path = f"data/test_{unique_id}.db"
                    _fallback_files.append(actual_db_path)
                    print(f"⚠️  Could not delete {base_db_path} - falling back to {actual_db_path}")
                    break

    # Update repo to use the actual path we decided on
    os.environ["DATABASE_PATH"] = actual_db_path
    repo.db_path = actual_db_path

    # 3. Re-initialize tables on the actual file
    with sqlite3.connect(actual_db_path) as conn:
        _create_tables(conn)
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📊 Tables in database {actual_db_path}: {[table[0] for table in tables]}")
    
    # CRITICAL WINDOWS FIX: Explicitly close the setup connection to release the file lock
    conn.close()
    
    yield
    
    # 4. Cleanup after tests
    print("\n🧹 Test completed, cleaning up...")
    
    # Force one more cleanup before deleting
    repo.cleanup()
    gc.collect()
    time.sleep(0.2)  # Give OS time to release handles
    
    # Try to clean up the main file
    repo.cleanup(force_delete=True)
    
    # Clean up any fallback files
    for fallback_file in _fallback_files:
        try:
            if os.path.exists(fallback_file):
                # Try multiple times
                for attempt in range(3):
                    try:
                        os.remove(fallback_file)
                        print(f"✅ Cleaned up fallback file: {fallback_file}")
                        break
                    except PermissionError:
                        if attempt < 2:
                            time.sleep(0.2)
                            gc.collect()
                        else:
                            print(f"⚠️  Could not clean up {fallback_file}")
        except Exception as e:
            print(f"⚠️  Could not clean up {fallback_file}: {e}")

def _create_tables(conn):
    """Helper to create all tables"""
    # Create prompts table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            version TEXT NOT NULL,
            content TEXT NOT NULL,
            active BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """)
    
    # Create metrics table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            value REAL,
            dimensions TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create conversations table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY,
            tenant_id TEXT NOT NULL,
            lead_id TEXT NOT NULL,
            messages TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            metadata TEXT
        )
    """)
    
    # Create dead_letter_queue table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS dead_letter_queue (
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
    
    conn.commit()
    print("✅ Database tables created/verified")

@pytest.fixture
def sample_tenant():
    """Provide a sample tenant ID for tests"""
    return "test_tenant_123"

@pytest.fixture
def rate_limiter():
    return RateLimiter(window_seconds=1)  # Fast tests

@pytest.fixture
def mock_groq(monkeypatch):
    """Mock Groq client - injected directly without magic wrappers."""
    from app.outreach_agent import outreach_agent
    
    # 1. Create a mock usage object
    mock_usage = MagicMock(
        prompt_tokens=10,
        completion_tokens=5,
        total_tokens=15
    )
    
    # 2. Create the completion response with the required schema_version
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='{"message": "Hello from mock", "confidence_score": 0.9, "schema_version": "1.0"}'
            )
        )
    ]
    mock_completion.usage = mock_usage
    
    # 3. Setup the fake client
    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_completion)
    
    # 4. Swap the live client with the fake client directly
    monkeypatch.setattr(outreach_agent, "client", mock_client)
    
    yield mock_client