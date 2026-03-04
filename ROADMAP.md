# JobsFinder Roadmap

## Vision
An AI-powered job search assistant that understands your background, asks the right questions, and finds the best opportunities for you — without you having to know exactly what to search for.

---

## ✅ Completed

### Phase 1 — AI-Powered Natural Language Search
Replace fragile regex parsing with LLM-based query understanding.
- Groq (LLaMA 3.1) parses natural language into structured search parameters
- Any phrasing works: "find senior cybersecurity jobs in remote", "React roles in Vancouver", etc.
- Unit tests with mocked API calls

### Phase 2 — Conversational Responses + Frontend Cleanup
- Groq generates natural, conversational summaries of job results
- Frontend routes all messages through `/api/chat` — no more client-side parsing
- Version string in UI header
- Swapped Anthropic API for Groq (free tier, no credit card required)

### Career Advisor Phase A — Resume Input UI
- New tabbed UI: Job Search tab and Career Advisor tab
- Career Advisor accepts resume via paste or PDF upload
- Refactored App.js into clean separate components

---

## 🔜 In Progress

### Career Advisor Phase B — Resume Analysis + Clarifying Questions
- Backend analyzes resume text using Groq
- Extracts skills, experience level, and possible job directions
- Asks 2-3 clarifying questions (e.g. IC vs management, remote vs hybrid)
- Multi-turn conversation history (absorbs original Phase 3)
- Frontend wires up the clarifying questions flow

---

## 📋 Planned

### Career Advisor Phase C — Multi-Search + Combined Results
- Groq suggests multiple job titles based on resume + answers
- Parallel Adzuna searches for each suggested title
- Combined, deduplicated results grouped by job category
- Presented conversationally with context from the resume analysis

### Phase 4 — Cover Letter Builder
- User selects a job from results
- Groq generates a tailored cover letter based on the job description and resume
- Editable in the UI before copying or downloading

---

## 🐛 Known Issues

### KI-001: No conversational context in Job Search tab
**Status:** Open — planned fix in Career Advisor Phase B  
**Description:** Follow-up messages in the Job Search tab lose prior search context.  
**Example:** User searches "cybersecurity jobs in Ottawa", then says "how about remote instead?" — the job title is lost and the search returns no results.

---

## Architecture
See `ARCHITECTURE.md` for a full diagram and explanation of technical decisions.
