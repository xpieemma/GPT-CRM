# Database Seeding

Two seed scripts for different purposes.

## Quick Reference

| Script | Time | Use When |
|--------|------|----------|
| `seed_dev.py` | ~1s | Daily development, running tests |
| `seed_demo.py` | ~30s | Interviews, demos, screenshots |

## Usage

### Windows (double-click)
- `seed-dev.bat` — dev data
- `seed-demo.bat` — demo data

### Command line
```bash
python scripts/seed.py              # dev (default)
python scripts/seed.py --type demo  # demo data
python scripts/seed.py --type all   # both
```

## What Each Creates

### seed_dev.py
- 1 tenant (`dev`)
- 1 active prompt
- 2 cost metrics
- 1 conversation

### seed_demo.py
- 3 tenants: `enterprise_co`, `startup_io`, `agency_inc`
- Distinct prompt per tenant
- 7 days of cost history (different usage patterns per tenant)
- 30 leads with 2–4 conversation turns each
- 5 Dead Letter Queue failures
- `startup_io` seeded over its daily budget limit

## Production Safety

Both scripts check `ENVIRONMENT=production` and refuse to run without `--force`.
