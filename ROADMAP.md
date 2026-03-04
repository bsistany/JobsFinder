# JobsFinder Roadmap

> **For AI assistants:** This file is the persistent memory for this project.
> Read it at the start of every session to get full context before touching any code.

---

## Vision
An AI-powered job search assistant that understands your background, asks the right
questions, and finds the best opportunities — without the user needing to know exactly
what to search for.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React | Industry standard, component-based, scales well |
| Backend | FastAPI (Python) | Async, AI/ML ecosystem, auto-generates API docs at `/docs` |
| AI / NLP | Groq API (LLaMA 3.1) | Free tier, fast inference, OpenAI-compatible. Originally Anthropic Claude — swapped due to billing friction. Easy to swap back. |
| Job Data | Adzuna API | Real Canadian job data, free tier available |
| Containerization | Docker + docker-compose | Frontend and backend as separate containers |
| Testing | pytest + pytest-asyncio | Unit tests with mocked API calls — no cost, no network dependency |

---

## Project Structure

```
job-search-ai/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI routes
│   │   ├── claude_service.py    # Groq/LLM calls (parse queries, format responses)
│   │   └── adzuna_service.py    # Adzuna job search API calls
│   ├── tests/
│   │   └── test_claude_service.py  # Unit tests (8 tests, all passing)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env                     # GROQ_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY (never committed)
├── frontend/
│   ├── src/
│   │   ├── App.js               # Main React app (JobSearchTab, CareerAdvisorTab, App)
│   │   └── App.css              # All styles
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── ROADMAP.md                   # This file
├── ARCHITECTURE.md              # Architecture diagram and decisions (to be created)
├── README.md
└── .gitignore                   # .env, node_modules, __pycache__ excluded
```

---

## Key Decisions Log

| Decision | Choice | Reason |
|---|---|---|
| AI provider | Groq (LLaMA 3.1) | Anthropic billing declined; Groq is free tier, one-line swap back |
| Model | `llama-3.1-8b-instant` | `llama3-8b-8192` was decommissioned |
| Job data | Adzuna | Free tier, Canadian coverage, straightforward API |
| No database yet | — | Not needed until user accounts / saved jobs feature |
| All AI calls via backend | FastAPI only | API keys never exposed to frontend |
| Groq class name | `ClaudeService` in `claude_service.py` | Kept name to avoid breaking imports; easy to rename later |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Version and feature info |
| GET | `/health` | Health check |
| POST | `/api/chat` | Main chat endpoint — Claude parses intent, calls Adzuna, formats response |
| GET | `/api/jobs/search` | Direct Adzuna job search |
| POST | `/api/jobs/search` | Direct Adzuna job search (POST) |
| GET | `/api/jobs/categories` | Adzuna job categories |

---

## ✅ Completed

### Phase 1 — AI-Powered Natural Language Search
- Groq (LLaMA 3.1) parses natural language into structured `{what, where}` params
- Replaces fragile regex parsing — any phrasing now works
- Unit tests with mocked API calls (5 tests)

### Phase 2 — Conversational Responses + Frontend Cleanup
- Groq generates natural conversational summaries of job results
- Frontend routes all messages through `/api/chat` — no client-side parsing
- Version string displayed in UI header (`· v0.4.0`)
- Swapped Anthropic → Groq
- Unit tests expanded to 8 total

### Career Advisor Phase A — Resume Input UI
- Tabbed UI: 🔍 Job Search | 🎯 Career Advisor
- Career Advisor tab: paste resume text or upload PDF (upload UI only — parsing in Phase B)
- App.js refactored into `JobSearchTab`, `CareerAdvisorTab`, `App` components

---

## 🔜 In Progress

### Career Advisor Phase B — Resume Analysis + Clarifying Questions
- [ ] New backend endpoint `POST /api/advisor/analyze` — receives resume text, returns extracted profile + clarifying questions
- [ ] New backend endpoint `POST /api/advisor/search` — receives resume + answers, returns suggested job titles
- [ ] Groq extracts: skills, experience level, possible job directions
- [ ] 2-3 clarifying questions (e.g. IC vs management, remote vs hybrid)
- [ ] Multi-turn conversation history in advisor session (absorbs original Phase 3)
- [ ] Frontend wires up clarifying questions flow after resume submission

---

## 📋 Planned

### Career Advisor Phase C — Multi-Search + Combined Results
- Groq suggests multiple job titles based on resume + clarifying answers
- Parallel Adzuna searches for each title
- Combined deduplicated results grouped by job category
- Conversational presentation with resume context

### Phase 4 — Cover Letter Builder
- User selects a job from results
- Groq generates a tailored cover letter using job description + resume
- Editable in UI before copying or downloading

---

## 🐛 Known Issues

### KI-001: No conversational context in Job Search tab
**Status:** Open — fix planned in Career Advisor Phase B
**Description:** Follow-up messages lose prior search context.
**Example:** Search "cybersecurity jobs in Ottawa" → "how about remote instead?" loses the job title, returns no results.

---

## Running the App

```bash
# Start
docker-compose up

# Start with rebuild (after dependency changes)
docker-compose down && docker-compose up --build

# Run tests
docker-compose exec backend pytest tests/

# View API docs
open http://localhost:8000/docs

# View app
open http://localhost:3000
```
