# Engineering Philosophy: Honest Abstractions

This codebase follows a consistent philosophy:

## 1. Make Limitations Visible
Every component that has a production limitation documents it explicitly.
No pretending in-memory storage is "just like Redis."

## 2. Provide the Upgrade Path
Each limitation includes an explanation of what would change in production.
Shows we know the right tool, even if we're not using it.

## 3. Test Fast, Test Real
- Configurable windows for rate limit tests (1s not 60s)
- No JSON1 dependencies (works on all SQLite)
- Environment variables for test configuration

## 4. Consistency Over Cleverness
- Use tenant_id columns everywhere (not JSON extraction)
- Pass async handlers directly (no unnecessary wrappers)
- Document cache behavior (lru_cache caveats explained)

## 5. Interview-Ready Documentation
Every trade-off is framed as a talking point:
"We used X for the demo, but here's exactly why production would use Y."

This approach demonstrates senior thinking without over-engineering
a free portfolio project.
