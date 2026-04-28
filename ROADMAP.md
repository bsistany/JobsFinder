# JobsFinder Roadmap

> **For AI assistants:** This file is the persistent memory for this project.
> Read it at the start of every session to get full context before touching any code.

---

## Vision
A personal job match pipeline: store your profile once, auto-fetch and score jobs from
Adzuna against your profile, see only ≥70% matches, generate tailored resume notes and
cover letters on approval, and track applications — all in one tool.

---

## Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Frontend | React | IBM Plex Mono/Sans, dark industrial theme |
| Backend | FastAPI (Python) | Async, auto-docs at `/docs` |
| AI / NLP | Groq API (llama-3.1-8b-instant) | Free tier. Smart truncation per call (see scoring notes) |
| Job Data | Adzuna API | Canadian (`ca`) by default |
| DB | SQLite via aiosqlite | 4 tables: profile, job_titles, applications, advisor_session |
| Containerization | Docker + docker-compose | Frontend + backend, SQLite mounted as volume |

---

## Project Structure

```
JobsFinder/
├── backend/
│   ├── app/
│   │   ├── main.py              # All FastAPI routes (pipeline + existing advisor/search)
│   │   ├── pipeline_service.py  # Groq calls: analyze, score, generate docs
│   │   ├── claude_service.py    # KEPT — Groq calls for Career Advisor tab (untouched)
│   │   ├── adzuna_service.py    # KEPT — Adzuna job search (untouched)
│   │   └── database.py         # SQLite init, migration, all DB helpers
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env                    # GROQ_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY
├── frontend/
│   ├── src/
│   │   ├── App.js              # Full pipeline UI + preserved advisor/search tabs
│   │   └── App.css             # Dark industrial theme (IBM Plex Mono/Sans)
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── ROADMAP.md
├── my_docs/                    # gitignored — local private documents
│   ├── Bahman-Sistany-Intro.txt
│   ├── Bahman-Sistany-resume-2026-V04.txt
│   └── cover_letter_themes.txt (planned)
└── database/                   # SQLite DB mounted here (job_search.db)
```

---

## Key Decisions Log

| Decision | Choice | Reason |
|---|---|---|
| AI provider | Groq (llama-3.1-8b-instant) | Free tier, fast |
| Scoring truncation | intro ≤180w + resume ≤350w + JD ≤280w + themes ≤80w | Keeps scoring calls under 1000 tokens |
| Profile inputs | intro + resume + career narrative + location prefs | File upload or paste; all stored in DB |
| Score threshold | 70% hard filter | Sub-70 dropped silently — user only sees qualified leads |
| Location scoring | preferred/acceptable/excluded tiers | 20% of score; Remote always preferred unless excluded |
| Career narrative | Optional third doc from NotebookLM analysis | Improves voice matching in cover letter generation |
| Job titles | Stored in DB, advisor-driven setup + manual edit | Run advisor once to bootstrap, manage on-demand after |
| Advisor session | Persisted to DB | Setup state survives navigation and page refresh |
| Generation timing | On approval only | Never bulk-generate — one job at a time, user-triggered |
| Career Advisor tab | Kept untouched | Separate feature for general users; not part of pipeline |
| DB | SQLite (aiosqlite) | Already in docker-compose, no new infra needed |
| Frontend nav | Sidebar with pipeline views + general tabs | Pipeline is primary; advisor/search secondary |

---

## Database Schema

### `profile` (single row, id=1)
- `id`, `intro_text`, `resume_text`, `themes_text`
- `locations_preferred` (comma-sep, default: `Remote`)
- `locations_acceptable` (comma-sep)
- `locations_excluded` (comma-sep)
- `updated_at`

### `job_titles`
- `id`, `title`, `added_at`

### `applications`
- `id` (Adzuna job id), `title`, `company`, `location`, `description`
- `salary_min`, `salary_max`, `redirect_url`
- `score` (0-100), `score_reason`
- `status`: `queued` → `approved`/`rejected` → `drafted` → `applied`/`no_response`
- `resume_notes`, `cover_letter`
- `created_at`, `updated_at`

### `advisor_session` (single row, id=1)
- `id`, `stage`, `data` (JSON blob), `updated_at`
- Persists setup flow state across navigation

---

## API Endpoints

### Pipeline
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/pipeline/profile` | Read or upsert full profile |
| POST | `/api/pipeline/setup/analyze` | Advisor analyzes profile, returns suggested titles + questions |
| POST | `/api/pipeline/setup/refine` | Takes Q&A answers, returns final confirmed title list |
| GET/POST/DELETE | `/api/pipeline/setup/session` | Persist/restore/clear advisor session |
| GET/POST | `/api/pipeline/titles` | Get or replace full title list |
| POST | `/api/pipeline/titles/add` | Add one title |
| DELETE | `/api/pipeline/titles/{id}` | Remove one title |
| POST | `/api/pipeline/run` | Fetch from Adzuna, score all, persist ≥70% as queued |
| GET | `/api/pipeline/queue` | Get queued applications |
| POST | `/api/pipeline/queue/{id}/decide` | approve or reject |
| POST | `/api/pipeline/generate/{id}` | Generate resume notes + cover letter |
| GET | `/api/pipeline/tracker` | All applications |
| PATCH | `/api/pipeline/tracker/{id}/status` | Update status |
| POST | `/api/pipeline/tracker/{id}/docs` | Save edited docs |

### Preserved (unchanged)
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/chat` | NL job search chat |
| GET/POST | `/api/jobs/search` | Direct Adzuna search |
| GET | `/api/jobs/categories` | Adzuna categories |
| POST | `/api/advisor/analyze` | Career advisor resume analysis |
| POST | `/api/advisor/suggest` | Career advisor job suggestions |

---

## ✅ Completed

### v0.1–v0.5 (pre-pipeline)
- NL job search via Groq + Adzuna
- Career Advisor tab (resume analysis → clarifying questions → job title suggestions)
- Docker setup, tests

### v0.6.0 — Personal Job Match Pipeline
- `database.py` — SQLite init, profile/titles/applications helpers
- `pipeline_service.py` — Groq scoring, advisor-driven title analysis, doc generation
- `main.py` — all pipeline routes added, existing routes preserved
- `App.js` — full rebuild: sidebar nav, Profile, Setup, Pipeline, Tracker views
- `App.css` — dark industrial theme with IBM Plex Mono/Sans

### v0.7.0 — Profile Enrichment + Location Filtering
- `database.py` — added `themes_text`, `locations_preferred/acceptable/excluded` to profile; `advisor_session` table; safe ALTER TABLE migration
- `pipeline_service.py` — location penalty in scoring (20% weight); themes context in scoring, resume notes, cover letter
- `main.py` — profile API accepts all new fields; generation passes themes; scoring passes location + themes
- `App.js` — file upload for all doc fields; career narrative field; structured location tier editor (pills); advisor session persisted to DB

---

## 🔜 Planned

### v0.8 — Pipeline Quality
- [ ] Pagination in pipeline run (fetch more than 10/title)
- [ ] Re-score existing queued jobs when profile changes
- [ ] Pipeline run history (timestamp, counts per run)
- [ ] Export tracker to CSV
- [ ] Batch approve with one click

### v0.9 — Content Quality
- [ ] Notes field per application (free text, interview prep)
- [ ] Interview stage tracking
- [ ] PDF upload support (parse resume/intro from PDF directly)

---

## 🐛 Known Issues

### KI-001: No conversational context in Job Search tab
**Status:** Open — chat tab loses context between messages.

### KI-002: Adzuna description truncated at 500 chars
**Status:** By design in adzuna_service.py — sufficient for scoring, may miss nuance.

### KI-003: Adzuna email popup on job view
**Status:** Known — click "No Thanks" to proceed to the posting. Warning shown in UI.

---

## Running the App

```bash
# Start
docker compose up

# Rebuild after code changes (requirements.txt, Dockerfile, package.json)
docker compose down && docker compose up --build

# Restart backend only (after .py file changes if hot-reload missed)
docker compose restart backend

# Run tests
docker compose exec backend pytest tests/

# API docs
open http://localhost:8000/docs

# App
open http://localhost:3000
```

## When to rebuild vs reload

| Change type | Action needed |
|---|---|
| `.py` files | Auto hot-reload (uvicorn watches) |
| `.js` / `.css` files | Auto hot-reload (webpack watches) |
| `requirements.txt` | `docker compose up --build` |
| `Dockerfile` | `docker compose up --build` |
| `package.json` | `docker compose up --build` |
| New DB columns | `docker compose restart backend` (migration runs on startup) |

## First-Run Checklist

1. **Profile** → load or paste intro doc + resume → set location preferences → Save
2. **Search Setup** → run advisor → deselect irrelevant titles → answer questions → confirm
3. **Pipeline** → run now → review queue → approve or generate docs directly
4. **Tracker** → update status as you progress through applications

## my_docs/ contents (gitignored)

```
my_docs/
├── Bahman-Sistany-Intro.txt           # intro document
├── Bahman-Sistany-resume-2026-V04.txt # current resume
└── cover_letter_themes.txt            # planned — NotebookLM output from past cover letters
```
