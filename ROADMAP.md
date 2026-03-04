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
│   │   ├── claude_service.py    # Groq/LLM calls (parse queries, format responses, advisor)
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
├── ROADMAP.md                   # This file — persistent memory across sessions
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
| Advisor flow | Conversational chat, not rigid form | User needs to correct/challenge AI profile assessment freely |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Version and feature info |
| GET | `/health` | Health check |
| POST | `/api/chat` | Main chat — Groq parses intent, calls Adzuna, formats response |
| GET | `/api/jobs/search` | Direct Adzuna job search |
| POST | `/api/jobs/search` | Direct Adzuna job search (POST) |
| GET | `/api/jobs/categories` | Adzuna job categories |
| POST | `/api/advisor/analyze` | Analyze resume text, return profile + clarifying questions |
| POST | `/api/advisor/chat` | Conversational advisor chat with resume + history context |

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

### Career Advisor Phase B (partial) — Resume Analysis
- New backend endpoint `POST /api/advisor/analyze` — returns candidate profile + clarifying questions
- New backend endpoint `POST /api/advisor/suggest` — returns job title suggestions based on profile + answers
- Multi-stage frontend flow: Input → Analyzing → Questions → Suggesting → Ready
- Version bumped to `0.5.0`

---

## 🔜 In Progress

### Career Advisor Phase B (revised) — Conversational Advisor Chat
Replacing the rigid questions form with a free-form chat interface after resume analysis.

**Why the change:** Initial profile assessment can be wrong (e.g. misidentified experience level).
User needs to be able to challenge, correct, and refine the profile conversationally before searching.

**New flow:**
```
Resume input
    ↓
AI analyzes → profile summary shown (scrollable, pinned at top)
    ↓
Chat window opens below (like Job Search tab)
    ↓
User chats freely:
  - "why did you say intermediate? I have 20 years experience"
  - "change location to remote"
  - "looks good, find my jobs now"
    ↓
AI responds, updates profile if needed
AI detects "find jobs" intent → triggers job title suggestions automatically
```

**Implementation plan:**
- [ ] New `POST /api/advisor/chat` endpoint — accepts resume text + conversation history + latest message
- [ ] New `advisor_chat()` method in `claude_service.py` — handles profile updates, Q&A, and intent detection
- [ ] Frontend: replace rigid stage form with pinned profile summary + chat window
- [ ] Remove `/api/advisor/suggest` endpoint (absorbed into advisor chat flow)
- [ ] AI detects "ready to search" intent and returns structured job suggestions in same response

---

## 📋 Planned

### Career Advisor Phase C — Multi-Search + Combined Results
- Backend runs parallel Adzuna searches for each suggested job title
- Combined deduplicated results grouped by job category
- Conversational presentation with resume context

### Phase 4 — Cover Letter Builder
- User selects a job from results
- Groq generates a tailored cover letter using job description + resume
- Editable in UI before copying or downloading

---

## 🐛 Known Issues

### KI-001: No conversational context in Job Search tab
**Status:** Open — will be addressed after Career Advisor chat is built (same pattern)
**Description:** Follow-up messages lose prior search context.
**Example:** Search "cybersecurity jobs in Ottawa" → "how about remote instead?" loses the job title.

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
