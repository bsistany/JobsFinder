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
| AI / NLP | Groq API (llama-3.1-8b-instant) | Free tier. Smart truncation: intro ≤200w, resume ≤400w, JD ≤300w per scoring call |
| Job Data | Adzuna API | Canadian (`ca`) by default |
| DB | SQLite via aiosqlite | 3 tables: profile, job_titles, applications |
| Containerization | Docker + docker-compose | Frontend + backend + postgres (postgres unused, SQLite active) |

---

## Project Structure

```
JobsFinder/
├── backend/
│   ├── app/
│   │   ├── main.py              # All FastAPI routes (pipeline + existing advisor/search)
│   │   ├── pipeline_service.py  # NEW — Groq calls for pipeline: analyze, score, generate
│   │   ├── claude_service.py    # KEPT — Groq calls for Career Advisor tab (untouched)
│   │   ├── adzuna_service.py    # KEPT — Adzuna job search (untouched)
│   │   └── database.py         # NEW — SQLite init, helpers for profile/titles/applications
│   ├── tests/
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env                    # GROQ_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY
├── frontend/
│   ├── src/
│   │   ├── App.js              # Full rebuild — pipeline UI + preserved advisor/search tabs
│   │   └── App.css             # Dark industrial theme (IBM Plex, monospace)
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── ROADMAP.md
└── database/                   # SQLite DB mounted here (job_search.db)
```

---

## Key Decisions Log

| Decision | Choice | Reason |
|---|---|---|
| AI provider | Groq (llama-3.1-8b-instant) | Free tier, fast |
| Scoring truncation | intro ≤200w + resume ≤400w + JD ≤300w | Keeps each scoring call under 1000 tokens, safe on free tier |
| Profile inputs | intro doc + resume (both text) | User maintains one intro doc + resume, pasted once |
| Score threshold | 70% hard filter | Sub-70 dropped silently — user only sees qualified leads |
| Job titles | Stored in DB, advisor-driven setup + manual edit | Run advisor once to bootstrap, manage titles on-demand after |
| Generation timing | On approval only | Never bulk-generate — one job at a time, user-triggered |
| Career Advisor tab | Kept untouched | Separate feature for general users; not part of pipeline |
| DB | SQLite (aiosqlite) | Already in docker-compose, no new infra |
| Frontend nav | Sidebar with pipeline views + general tabs | Pipeline is primary; advisor/search secondary |

---

## Database Schema

### `profile` (single row, id=1)
- `id`, `intro_text`, `resume_text`, `updated_at`

### `job_titles`
- `id`, `title`, `added_at`

### `applications`
- `id` (Adzuna job id), `title`, `company`, `location`, `description`
- `salary_min`, `salary_max`, `redirect_url`
- `score` (0-100), `score_reason`
- `status`: `queued` → `approved`/`rejected` → `drafted` → `applied`/`no_response`
- `resume_notes`, `cover_letter`
- `created_at`, `updated_at`

---

## API Endpoints

### Pipeline (new)
| Method | Endpoint | Description |
|---|---|---|
| GET/POST | `/api/pipeline/profile` | Read or upsert intro + resume |
| POST | `/api/pipeline/setup/analyze` | Advisor analyzes profile, returns suggested titles + questions |
| POST | `/api/pipeline/setup/refine` | Takes Q&A answers, returns final confirmed title list |
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

---

## 🔜 Planned

### v0.7 — Quality of Life
- [ ] PDF upload support (parse resume from PDF)
- [ ] Pagination in pipeline run (fetch more than 10/title)
- [ ] Re-score existing queued jobs against updated profile
- [ ] Pipeline run history (when did last run happen, how many found)
- [ ] Email / export tracker to CSV

### v0.8 — Enhancements
- [ ] Batch approve with one click
- [ ] Notes field per application (free text)
- [ ] Interview stage tracking

---

## 🐛 Known Issues

### KI-001: No conversational context in Job Search tab
**Status:** Open — chat tab loses context between messages.

### KI-002: Adzuna description truncated at 500 chars
**Status:** By design in adzuna_service.py — sufficient for scoring, may miss nuance.

---

## Running the App

```bash
# Start
docker compose up

# Rebuild after code changes
docker compose down && docker compose up --build

# Run tests
docker compose exec backend pytest tests/

# API docs
open http://localhost:8000/docs

# App
open http://localhost:3000
```

## First-Run Checklist

1. Open app → **Profile** → paste your intro doc + resume → Save
2. Open **Search Setup** → click "run advisor" → answer questions → confirm titles
3. Open **Pipeline** → click "run now" → review queue → approve jobs you want
4. Click "generate docs" on any approved job → edit notes + cover letter → save
5. Open **Tracker** → update status as you apply
