"""Rich demo data for interviews - shows full capabilities"""
import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta

# Allow running from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.repository import repo
from app.services.dead_letter_queue import dlq
from app.models import LeadStatus


def seed_demo(force=False):
    """Rich demo data showing multi-tenancy, costs, failures"""

    if os.getenv("ENVIRONMENT") == "production" and not force:
        print("Cannot seed production without --force")
        return

    print("Seeding DEMO database...")
    print("Shows: multi-tenancy, cost tracking, DLQ, audit trails")
    print()

    # 1. Three tenants with distinct personalities
    tenants = {
        "enterprise_co": {"budget": 100.00, "industry": "Finance"},
        "startup_io":    {"budget": 20.00,  "industry": "SaaS"},
        "agency_inc":    {"budget": 50.00,  "industry": "Marketing"},
    }

    prompt_templates = {
        "enterprise_co": "You are a formal enterprise agent. Use professional language.",
        "startup_io":    "You are a casual startup agent. Be friendly and energetic.",
        "agency_inc":    "You are a creative agency agent. Focus on marketing angles.",
    }

    for tenant_id, config in tenants.items():
        repo.create_prompt(
            tenant_id=tenant_id,
            version="v1.0.0",
            content=prompt_templates[tenant_id],
            active=True,
            metadata={"industry": config["industry"]}
        )

    # 2. Seven days of cost history (shows budget tracking over time)
    print("Generating 7 days of cost history...")
    db_path = os.getenv("DATABASE_PATH", "data/outreach.db")

    daily_volumes = {
        "enterprise_co": (40, 60),   # Heavy usage
        "startup_io":    (5, 15),    # Light usage
        "agency_inc":    (20, 35),   # Medium usage
    }

    for tenant_id, (lo, hi) in daily_volumes.items():
        for days_ago in range(7, 0, -1):
            date = datetime.now() - timedelta(days=days_ago)
            for _ in range(random.randint(lo, hi)):
                cost = random.uniform(0.02, 0.08)
                with sqlite3.connect(db_path) as conn:
                    conn.execute(
                        "INSERT INTO metrics (tenant_id, metric_name, value, timestamp) VALUES (?, ?, ?, ?)",
                        (tenant_id, "TokenCost", cost, date)
                    )

    # 3. Thirty leads with multi-turn conversation history
    print("Generating 30 leads with conversation history...")
    positions = ["CTO", "VP Sales", "CEO", "Product Lead"]
    company_prefixes = ["Tech", "Data", "Cloud", "Scale", "Edge"]

    for i in range(30):
        tenant_id = random.choice(list(tenants.keys()))
        lead_id = f"lead_{1000 + i}"

        context = {
            "lead": {
                "id": lead_id,
                "first_name": f"Contact_{i}",
                "last_name": "Smith",
                "email": f"contact{i}@example.com",
                "company": f"{random.choice(company_prefixes)} Corp",
                "position": random.choice(positions),
                "status": random.choice([s.value for s in LeadStatus]),
            }
        }

        for turn in range(random.randint(2, 4)):
            repo.log_conversation(
                tenant_id=tenant_id,
                lead_id=lead_id,
                messages={
                    "context": context,
                    "response": {
                        "message": f"Follow-up message {turn + 1}",
                        "confidence_score": round(random.uniform(0.7, 0.99), 2),
                    }
                },
                metadata={
                    "prompt_version": "v1.0.0",
                    "cost_usd": round(random.uniform(0.001, 0.004), 4),
                    "turn": turn,
                }
            )

    # 4. DLQ failures (shows error-handling paths)
    print("Adding 5 Dead Letter Queue failures...")
    failure_reasons = [
        "Connection timeout",
        "Rate limit exceeded",
        "CRM API unavailable",
    ]

    for i in range(5):
        tenant_id = random.choice(["enterprise_co", "agency_inc"])
        dlq.push(
            queue_name="webhook_failures",
            payload={"event": "crm_update", "attempt": i + 1},
            tenant_id=tenant_id,
            error=random.choice(failure_reasons),
            metadata={"retry_count": i}
        )

    # 5. Push startup_io close to (and over) daily budget limit
    repo.record_metric("startup_io", "TokenCost", 18.50)
    repo.record_metric("startup_io", "TokenCost", 1.80)

    print()
    print("DEMO SEED COMPLETE")
    print()
    print("What's been created:")
    print("  3 tenants  - enterprise_co, startup_io, agency_inc")
    print("  7 days     - cost history per tenant")
    print("  30 leads   - with 2-4 conversation turns each")
    print("  5 failures - in the Dead Letter Queue")
    print("  Budget hit - startup_io is over its daily limit")
    print()
    print("Try these curl commands after running run.bat:")
    print("  curl http://localhost:8000/api/tenant/stats -H 'X-Tenant-ID: enterprise_co'")
    print("  curl http://localhost:8000/api/tenant/stats -H 'X-Tenant-ID: startup_io'")
    print("  curl http://localhost:8000/api/tenant/stats -H 'X-Tenant-ID: agency_inc'")


if __name__ == "__main__":
    force = "--force" in sys.argv
    seed_demo(force=force)
