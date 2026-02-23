"""Minimal seed for local development - runs in <1 second"""
import os
import sys

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.repository import repo


def seed_development(force=False):
    """Quick seed for development - minimal data"""

    # Safety check
    if os.getenv("ENVIRONMENT") == "production" and not force:
        print("Cannot seed production without --force")
        return

    print("Seeding development database (quick)...")

    # 1. One tenant, one prompt
    repo.create_prompt(
        tenant_id="dev",
        version="v1.0.0",
        content="You are a development test agent.",
        active=True
    )

    # 2. Just a few metrics
    repo.record_metric("dev", "TokenCost", 0.05)
    repo.record_metric("dev", "TokenCost", 0.03)

    # 3. One test lead conversation
    repo.log_conversation(
        tenant_id="dev",
        lead_id="test_lead_1",
        messages={"test": "data"},
        metadata={"cost": 0.01}
    )

    print("Development seed complete")
    print("  Tenant: dev")
    print("  Run: python -m app.main")


if __name__ == "__main__":
    force = "--force" in sys.argv
    seed_development(force=force)
