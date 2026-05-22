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
| AI / NLP | Groq API (llama-3.1-8b-instant) | Free tier. Scoring, doc generation, career advisor |
| Semantic Search | sentence-transformers (all-MiniLM-L6-v2) | Local CPU inference, no API key, ~90MB model |
| Job Data | Adzuna API | Canadian (`ca`) by default |
| DB | SQLite via aiosqlite | 5 tables: profile, job_titles, applications, advisor_session, pipeline_runs |
| Containerization | Docker + docker-compose | Frontend + backend, SQLite mounted as volume |

---

## Project Structure

```
JobsFinder/
├── backend/
│   ├── app/
│   │   ├── main.py              # All FastAPI routes (pipeline + existing advisor/search)
│   │   ├── pipeline_service.py  # Groq calls: analyze, score, generate docs
│   │   ├── embedding_service.py # sentence-transformers: embed profile + jobs, cosine filter
│   │   ├── location.py          # Pure Python location normalizer and gate functions
│   │   ├── claude_service.py    # KEPT — Groq calls for Career Advisor tab (untouched)
│   │   ├── adzuna_service.py    # KEPT — Adzuna job search (untouched)
│   │   └── database.py         # SQLite init, migrations, all DB helpers
│   ├── tests/
│   │   └── test_location.py    # 63 unit tests for location normalizer and gate
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env                    # GROQ_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY
├── frontend/
│   ├── src/
│   │   ├── App.js              # Full pipeline UI + preserved advisor/search tabs
│   │   └── App.css             # Dark industrial theme (IBM Plex Mono/Sans)
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml           # Backend health check, frontend depends_on backend
├── ROADMAP.md
├── CONTRIBUTING.md              # Commit prefix convention
├── my_docs/                    # gitignored — local private documents
│   ├── Bahman-Sistany-Intro.txt
│   ├── Bahman-Sistany-resume-2026-V04.txt
│   └── cover_letter_themes.txt  # NotebookLM output from 16 past cover letters
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
| Location filtering | Python gate before Groq, not LLM instruction | Deterministic — LLM cannot override exclusions |
| Location tiers | Preferred: Ottawa, Remote / Excluded: everything else | Hard-coded in location.py, not stored in DB |
| City normalization | CITY_ALIASES dict + regex for remote/hybrid | Handles accents, suburbs, hybrid variants |
| Montreal | Removed from acceptable — now excluded | Too far; only Ottawa and Remote accepted |
| Career narrative | Optional third doc from NotebookLM analysis | Improves voice matching in cover letter generation |
| Job titles | 5-6 broad root titles stored in DB | Replaced 35+ exact titles — semantic pre-filter catches variants |
| Embedding model | all-MiniLM-L6-v2 (local, sentence-transformers) | No API cost, no data egress, ~90MB, sufficient quality |
| Fetch strategy | Broad root titles → location gate → embedding pre-filter → Groq scoring | Each layer cuts the pool; Groq only sees semantically relevant jobs |
| Embedding threshold | TBD during testing | Cosine similarity cutoff — tune to balance recall vs noise |
| Advisor session | Persisted to DB | Setup state survives navigation and page refresh |
| Generation timing | On approval only | Never bulk-generate — one job at a time, user-triggered |
| Career Advisor tab | Kept untouched | Separate feature for general users; not part of pipeline |
| DB | SQLite (aiosqlite) | Simple, no infra, mounted as volume |
| Docker | Backend health check + frontend depends_on | Reliable startup order, no race condition |
| Postgres | Removed | Was never used — we use SQLite |

---

## Location Rules (location.py)

**Preferred (full score)**
- Remote, work from home, WFH, fully remote, hybrid with no city
- Ottawa — including: Gatineau, Kanata, Nepean, Hull, Orléans, Gloucester
- Ottawa Hybrid → counts as Ottawa

**Excluded (hard drop, never reaches embedding or Groq)**
- Everything else — Montreal, Toronto, Vancouver, Calgary, Edmonton, Unknown, etc.
- Hybrid only gets credit for the city it's attached to
- "Hybrid - Vancouver" → Excluded
- "Hybrid - Montreal" → Excluded

**Normalization priority:**
1. Remote signals in location field
2. Known city in location field
3. Hybrid in location field → scan description → fallback Remote
4. Remote signals in first 600 chars of description
5. Known city in first 600 chars of description
6. "Unknown" → Excluded

---

## Pipeline Flow (v0.9.0)

```
Adzuna fetch (broad root titles, e.g. 10 results/title)
↓
Location gate (Python — excluded cities dropped, never reach embedding or Groq)
↓
Embedding pre-filter (cosine similarity vs profile vector — low-relevance jobs dropped)
↓
Groq scoring (full score 0-100 against intro + resume + themes)
↓
Queue ≥70% matches
```

---

## Database Schema

### `profile` (single row, id=1)
- `id`, `intro_text`, `resume_text`, `themes_text`
- `locations_preferred` (stored but not used for gate — gate uses location.py hardcoded rules)
- `locations_acceptable`, `locations_excluded`
- `updated_at`

### `job_titles`
- `id`, `title`, `added_at`

### `applications`
- `id` (Adzuna job id), `title`, `company`, `location` (normalized city), `description`
- `salary_min`, `salary_max`, `redirect_url`
- `score` (0-100), `score_reason`
- `status`: `queued` → `approved`/`rejected` → `drafted` → `applied`/`no_response`
- `resume_notes`, `cover_letter`
- `fetched_at`, `created_at`, `updated_at`

### `advisor_session` (single row, id=1)
- `id`, `stage`, `data` (JSON blob), `updated_at`
- Persists setup flow state across navigation

### `pipeline_runs`
- `id`, `run_at`, `fetched`, `location_excluded`, `embedding_filtered`, `scored`, `queued`, `dropped`
- One row per pipeline run — used for "last run at" display
- `embedding_filtered` added in v0.9.0

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
| POST | `/api/pipeline/titles/add` | Add one title (or multi-line paste) |
| DELETE | `/api/pipeline/titles/{id}` | Remove one title |
| POST | `/api/pipeline/run` | Fetch → location gate → embedding filter → score → queue ≥70% |
| GET | `/api/pipeline/last-run` | Last pipeline run summary |
| GET | `/api/pipeline/queue` | Get queued applications |
| DELETE | `/api/pipeline/queue/clear` | Clear queued jobs only (preserves approved/drafted/applied) |
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
- SQLite database layer
- Pipeline service (scoring, advisor, doc generation)
- All pipeline API routes
- Frontend rebuild: sidebar nav, Profile, Setup, Pipeline, Tracker

### v0.7.0 — Profile Enrichment + Location Filtering
- Career narrative field (NotebookLM output)
- File upload for all doc fields (load .txt)
- Structured location tier editor in Profile UI
- Location penalty in scoring (initially via Groq — later replaced)
- Advisor session persisted to DB

### v0.8.0 — Pipeline Hardening + Persistence
- `location.py` — pure Python location normalizer and hard exclusion gate
- 63 unit tests for location normalizer (`tests/test_location.py`)
- Python gate runs before Groq — excluded cities never consume API calls
- Queue sorted: Remote/Ottawa first, by score desc
- `pipeline_runs` table — last run timestamp and stats
- `fetched_at` on applications — shown on job cards
- "Clear queue" button — deletes only queued rows, preserves everything else
- "Last run at" banner on Pipeline page
- docker-compose: backend health check, frontend depends_on, Postgres removed
- Multi-line paste in title input — one title per line
- Montreal moved from acceptable to excluded
- Batch approve/reject with boolean keyword filter (AND, OR, NOT, parentheses)
- Generate docs moved from queue cards to Tracker (approved/drafted jobs only)
- CONTRIBUTING.md with commit prefix convention

### v0.9.0 — Semantic Search (branch: feature/semantic-search)
- Replace 35+ exact job titles with 5-6 broad root titles
- `embedding_service.py` — sentence-transformers (all-MiniLM-L6-v2), local CPU inference
- Profile vector computed once per pipeline run (intro + resume concatenated)
- Each post-gate job description embedded and compared via cosine similarity
- Embedding pre-filter drops irrelevant jobs before Groq scoring
- `embedding_filtered` count added to pipeline run stats and UI
- Similarity threshold tuned during testing

---

## 🔜 Planned

### v0.10 — Quality of Life
- [ ] Pagination in pipeline run (fetch more than 10/title)
- [ ] Re-score existing queued jobs when profile changes
- [ ] Export tracker to CSV
- [ ] Notes field per application (free text, interview prep)
- [ ] Interview stage tracking
- [ ] PDF upload support

---

## 🐛 Known Issues

### KI-001: No conversational context in Job Search tab
**Status:** Open — chat tab loses context between messages.

### KI-002: Adzuna description truncated at 500 chars
**Status:** By design in adzuna_service.py — sufficient for scoring, may miss nuance.

### KI-003: Adzuna email popup on job view
**Status:** Known — click "No Thanks" to proceed. Warning shown in UI.

### KI-004: Pre-gate jobs may appear in queue after DB wipe
**Status:** Resolved by doing full DB wipe (Option B) when location gate was deployed.
Future runs are clean — gate runs on every pipeline execution.

---

## Running the App

```bash
# Start (normal)
docker compose up

# First start or after orphan containers warning
docker compose up --remove-orphans

# Rebuild after requirements.txt / Dockerfile / package.json changes
docker compose down && docker compose up --build

# Restart backend only (after .py changes if hot-reload missed)
docker compose restart backend

# Run location tests
docker compose exec backend pytest tests/test_location.py -v

# Run all tests
docker compose exec backend pytest tests/ -v

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
| Full DB wipe | `docker compose down && rm database/job_search.db && docker compose up` |

## Normal Session Workflow

```
Open app → Pipeline page shows queue from last run
↓
Work through queue — approve, reject, generate docs
↓
Run pipeline again when you want fresh results
↓
No DB wipes, no re-saving profile, no re-adding titles
  unless something actually changed
```

## Fresh Start Workflow (after DB wipe)

1. **Profile** → load intro + resume + career narrative → set location tiers → Save
2. **Search Setup** → paste root titles (one per line) → add → verify count
3. **Pipeline** → run now → check location_excluded and embedding_filtered counts in stats
4. Work through queue

## my_docs/ contents (gitignored)

```
my_docs/
├── Bahman-Sistany-Intro.txt           # intro document
├── Bahman-Sistany-resume-2026-V04.txt # current resume
└── cover_letter_themes.txt            # NotebookLM output from 16 past cover letters
                                       # sections: value proposition, narrative,
                                       # job titles, consistent strengths, industries
```

## Version Tags

| Tag | Description |
|---|---|
| `v0.5.0-career-advisor` | Original — career advisor + job search |
| `v0.6.0-pipeline` | Personal job match pipeline |
| `v0.7.0-profile-enrichment` | Career narrative, file upload, location tiers |
| `v0.8.0-pipeline-hardening` | Python location gate, tests, persistence |
| `v0.9.0-semantic-search` | Sentence-transformers embedding pre-filter, broad root titles |
