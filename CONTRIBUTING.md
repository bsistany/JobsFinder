# Contributing

## Commit Convention

| Prefix | When to use |
|---|---|
| `feat:` | New capability (new endpoint, new UI view, new service method) |
| `fix:` | Bug fix |
| `refactor:` | Code restructure, no behavior change |
| `docs:` | ROADMAP, README, comments only |
| `chore:` | Dependencies, Docker, config, .gitignore |
| `test:` | Adding or updating tests |

---

## Author

**Bahman Sistany** — architecture, design decisions, implementation, code
review, integration, testing, and documentation.

GitHub: [github.com/bsistany](https://github.com/bsistany)

---

## Development Tools

This project was developed with assistance from AI coding tools. All design
decisions, code review, integration, and testing were performed by the author.

| Tool | Role | Scope |
|---|---|---|
| Claude (Anthropic) | Architecture design, code generation, debugging, sprint planning | All backend services, frontend UI, database schema, Docker setup, documentation |

---

## Third-Party Libraries & APIs

| Library / Service | License / Terms | Use |
|---|---|---|
| [FastAPI](https://fastapi.tiangolo.com) | MIT | Backend API framework |
| [aiosqlite](https://github.com/omnilib/aiosqlite) | MIT | Async SQLite access |
| [sentence-transformers](https://www.sbert.net) | Apache 2.0 | Local semantic embeddings (all-MiniLM-L6-v2) |
| [Groq API](https://groq.com) | Commercial (free tier) | LLM inference — scoring, doc generation, career advisor |
| [Adzuna API](https://developer.adzuna.com) | Commercial (free tier) | Job listing data |
| [React](https://react.dev) | MIT | Frontend UI |
