# GPT CRM Outreach Agent

A production-aware AI outreach system demonstrating :
multi-tenancy, budget enforcement, audit trails, dead letter queue, and rate limiting.

---

## Quick Start

```
1. setup.bat       ← run once to install dependencies and init database
2. Edit .env       ← add your OpenAI/Groq API key
3. seed-dev.bat    ← optional: load minimal dev data
4. run.bat         ← start the server at http://localhost:8000
5. test.bat        ← run the full test suite
```

For demos , use `seed-demo.bat` instead of `seed-dev.bat`.

---
## 🔑 Getting a FREE API Key

### Option 1: Groq (Fastest, No Credit Card) ⚡
1. Go to [console.groq.com](https://console.groq.com)
2. Click "Sign Up" (use Google/GitHub)
3. Go to API Keys section
4. Click "Create API Key"
5. Copy the key (starts with `gsk_`)
6. Add to `.env`: `PROVIDER=groq` and `GROQ_API_KEY=your_key`

### Option 2: Google Gemini (60 requests/min) ✨
1. Go to [makersuite.google.com/app/apikey](https://makersuite.google.com/app/apikey)
2. Sign in with Google account
3. Click "Get API Key"
4. Create new key
5. Add to `.env`: `PROVIDER=gemini` and `GEMINI_API_KEY=your_key`

### Option 3: OpenAI (Paid) 💰
Only if you already have credits. Add to `.env`: `PROVIDER=openai` and `OPENAI_API_KEY=your_key`

## Project Structure

```
GPT-CRM/
│
├── app/                            # Core application
│   ├── __init__.py
│   ├── main.py                     # FastAPI app, routes, middleware
│   ├── config.py                   # Settings via pydantic-settings + .env
│   ├── models.py                   # Pydantic models (Lead, AgentResponse, etc.)
│   ├── outreach_agent.py           # OpenAI integration with budget + audit
│   ├── crm_client.py               # CRM adapter (mock for demo)
│   ├── auth/
│   │   ├── __init__.py
│   │   └── oauth2.py               # OAuth2 scheme
│   ├── api/
│   │   ├── __init__.py
│   │   ├── dependencies.py         # Rate limiter, tenant extraction
│   │   ├── webhooks.py             # CRM webhook receiver
│   │   └── scheduler.py            # Meeting scheduler endpoint
│   ├── services/
│   │   ├── __init__.py
│   │   ├── repository.py           # SQLite, tenant-isolated queries
│   │   ├── audit.py                # Budget enforcement + audit trail
│   │   ├── dispatcher.py           # Background task dispatcher
│   │   ├── dead_letter_queue.py    # Persistent DLQ for failures
│   │   ├── prompt_store.py         # Prompt versioning
│   │   └── metrics.py              # Metric recording
│   └── utils/
│       ├── __init__.py
│       └── logging.py              # Structured logging
│
├── tests/                          # 40+ pytest tests
│   ├── __init__.py
│   ├── conftest.py                 # Fixtures, test DB setup/teardown
│   ├── test_repository.py
│   ├── test_audit.py
│   ├── test_dispatcher.py
│   ├── test_rate_limiting.py
│   ├── test_dead_letter_queue.py
│   ├── test_agent.py
│   └── test_integration.py
│
├── scripts/                        # Database seeding
│   ├── __init__.py
│   ├── seed_dev.py                 # Minimal data (~1 second)
│   ├── seed_demo.py                # Rich multi-tenant data (~30 seconds)
│   ├── seed.py                     # Combined runner (--type dev|demo|all)
│   └── README_SEED.md              # Seeding documentation
│
├── migrations/
│   └── init.sql                    # Full schema with indexes
│
├── data/
│   └── .gitkeep                    # outreach.db and test.db created at runtime
│
├── .env.example                    # Copy to .env and fill in keys
├── .gitignore
├── requirements.txt
├── requirements-test.txt
├── README.md
├── PHILOSOPHY.md
│
├── setup.bat                       # One-time setup
├── run.bat                         # Start server
├── test.bat                        # Run test suite
├── seed-dev.bat                    # Load dev seed data
└── seed-demo.bat                   # Load demo seed data
```

---

## Environment Setup

Copy `.env.example` to `.env` and fill in:

```env
GROQ_API_KEY=gsk_...
WEBHOOK_SECRET=any-random-string
JWT_SECRET_KEY=any-random-string
```

All other values have working defaults for local development.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | App info |
| GET | `/health` | Health check + DB status |
| POST | `/api/outreach/generate?lead_id=X` | Queue outreach generation |
| GET | `/api/task/{task_id}` | Poll task status |
| GET | `/api/tenant/stats` | Daily cost + DLQ stats |
| POST | `/webhooks/crm-update` | Receive CRM webhooks |
| POST | `/scheduler/meeting` | Schedule a meeting |

Pass `X-Tenant-ID: your-tenant` header to scope requests per tenant.

Interactive docs available at `http://localhost:8000/docs`.

---

## Seeding Data

**Development** — fast, one tenant, minimal rows:
```
seed-dev.bat
```

**Demo / Interview** — three tenants with history, failures, budget warnings:
```
seed-demo.bat
```

After running the demo seed, try:
```bash
curl http://localhost:8000/api/tenant/stats -H "X-Tenant-ID: enterprise_co"
curl http://localhost:8000/api/tenant/stats -H "X-Tenant-ID: startup_io"
curl http://localhost:8000/api/tenant/stats -H "X-Tenant-ID: agency_inc"
```

`startup_io` is seeded over its daily budget limit — the 402 budget enforcement is immediately visible.

---

## Architecture

```
Clients
  │
  ▼
FastAPI Gateway (main.py)
  ├── Rate limiter        per-tenant, configurable window
  ├── Auth                OAuth2 scheme (pluggable)
  ├── Middleware          request logging, metrics
  │
  ├── /api/outreach       → TaskDispatcher → OutreachAgent → OpenAI
  ├── /webhooks           → DLQ on failure
  └── /scheduler          → Meeting booking
        │
        ▼
  SQLite (tenant-isolated)
  ├── prompts             versioned per tenant
  ├── metrics             cost tracking
  ├── conversations       full audit trail
  └── dead_letter_queue   persistent failure log
```

---

## Engineering Trade-offs

| Pattern | This Project | Production Upgrade |
|---------|-------------|-------------------|
| Multi-tenancy | `WHERE tenant_id = ?` on every query | PostgreSQL Row-Level Security |
| Task queue | In-memory dict (single worker only) | Celery + Redis |
| Rate limiting | Configurable in-process window | Redis sliding window |
| Budget guard | SQLite `SUM()` (TOCTOU race) | Redis atomic Lua script |
| Settings cache | `lru_cache` (per process) | Shared config service |

Each limitation is documented inline in the relevant file.
