from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from app.adzuna_service import adzuna_service
from app.claude_service import claude_service
from app.pipeline_service import pipeline_service
from app import database as db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield

app = FastAPI(title="JobsFinder API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Models ───────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str
    jobs: Optional[list] = []
    job_count: Optional[int] = 0

class JobSearchQuery(BaseModel):
    what: Optional[str] = ""
    where: Optional[str] = ""
    page: Optional[int] = 1
    results_per_page: Optional[int] = 10

class ResumeAnalysisRequest(BaseModel):
    resume_text: str

class AdvisorAnswer(BaseModel):
    question_id: str
    question: str
    answer: str

class JobSuggestionsRequest(BaseModel):
    profile: dict
    answers: List[AdvisorAnswer]

class ProfileUpsert(BaseModel):
    intro_text: str
    resume_text: str
    themes_text: Optional[str] = ''
    locations_preferred: Optional[str] = 'Remote'
    locations_acceptable: Optional[str] = ''
    locations_excluded: Optional[str] = ''

class AnalyzeProfileRequest(BaseModel):
    intro_text: str
    resume_text: str

class RefineTitlesRequest(BaseModel):
    profile: dict
    suggested_titles: list
    answers: List[AdvisorAnswer]

class SetTitlesRequest(BaseModel):
    titles: List[str]

class AddTitleRequest(BaseModel):
    title: str

class PipelineRunRequest(BaseModel):
    results_per_page: Optional[int] = 10
    country: Optional[str] = "ca"

class DecideRequest(BaseModel):
    action: str

class UpdateStatusRequest(BaseModel):
    status: str

class SaveDocsRequest(BaseModel):
    resume_notes: str
    cover_letter: str

# ─── General ──────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "JobsFinder API",
        "status": "running",
        "version": "0.6.0",
        "features": ["career_advisor", "job_search", "pipeline", "application_tracker"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ─── Existing: Job Search ─────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    try:
        parsed = await claude_service.parse_job_search_query(message.message)
    except Exception as e:
        return ChatResponse(response=f"Sorry, I had trouble understanding that. (Error: {str(e)})")
    if not parsed.get("is_job_search"):
        return ChatResponse(response="I'm your job search assistant! Try: 'Find senior cybersecurity jobs in remote'.")
    result = await adzuna_service.search_jobs(what=parsed.get("what",""), where=parsed.get("where",""), results_per_page=10)
    if "error" in result:
        return ChatResponse(response=f"Search error: {result['error']}")
    jobs = result.get("jobs", [])
    count = result.get("count", 0)
    if not jobs:
        return ChatResponse(response="No results found. Try broader keywords.")
    try:
        summary = await claude_service.format_job_results(what=parsed.get("what",""), where=parsed.get("where",""), jobs=jobs, total_count=count)
    except Exception:
        summary = f"Found {count} jobs. Here are the top results:"
    return ChatResponse(response=summary, jobs=jobs, job_count=count)

@app.get("/api/jobs/search")
async def search_jobs(what: str = "", where: str = "", page: int = 1, results_per_page: int = 10):
    result = await adzuna_service.search_jobs(what=what, where=where, page=page, results_per_page=results_per_page)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/jobs/search")
async def search_jobs_post(query: JobSearchQuery):
    result = await adzuna_service.search_jobs(what=query.what, where=query.where, page=query.page, results_per_page=query.results_per_page)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/api/jobs/categories")
async def get_categories():
    return {"categories": await adzuna_service.get_job_categories()}

# ─── Existing: Career Advisor ─────────────────────────────────────────────────

@app.post("/api/advisor/analyze")
async def analyze_resume(request: ResumeAnalysisRequest):
    if not request.resume_text or len(request.resume_text.strip()) < 100:
        raise HTTPException(status_code=400, detail="Resume text is too short.")
    try:
        return await claude_service.analyze_resume(request.resume_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing resume: {str(e)}")

@app.post("/api/advisor/suggest")
async def suggest_jobs(request: JobSuggestionsRequest):
    try:
        return await claude_service.suggest_job_titles(profile=request.profile, answers=[a.dict() for a in request.answers])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error suggesting jobs: {str(e)}")

# ─── NEW: Pipeline — Profile ──────────────────────────────────────────────────

@app.get("/api/pipeline/profile")
async def get_profile():
    return {"profile": await db.get_profile()}

@app.post("/api/pipeline/profile")
async def save_profile(request: ProfileUpsert):
    if len(request.intro_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Intro text too short (min 50 chars).")
    if len(request.resume_text.strip()) < 100:
        raise HTTPException(status_code=400, detail="Resume text too short (min 100 chars).")
    return {"profile": await db.upsert_profile(
        intro_text=request.intro_text,
        resume_text=request.resume_text,
        themes_text=request.themes_text or '',
        locations_preferred=request.locations_preferred or 'Remote',
        locations_acceptable=request.locations_acceptable or '',
        locations_excluded=request.locations_excluded or '',
    )}

# ─── NEW: Pipeline — Setup ────────────────────────────────────────────────────

@app.post("/api/pipeline/setup/analyze")
async def pipeline_setup_analyze(request: AnalyzeProfileRequest):
    if len(request.intro_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Intro text too short.")
    if len(request.resume_text.strip()) < 100:
        raise HTTPException(status_code=400, detail="Resume text too short.")
    try:
        return await pipeline_service.analyze_profile(request.intro_text, request.resume_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing profile: {str(e)}")

@app.post("/api/pipeline/setup/refine")
async def pipeline_setup_refine(request: RefineTitlesRequest):
    try:
        return await pipeline_service.refine_titles(
            profile=request.profile,
            suggested_titles=request.suggested_titles,
            answers=[a.dict() for a in request.answers]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refining titles: {str(e)}")

@app.get("/api/pipeline/setup/session")
async def get_setup_session():
    return await db.get_advisor_session()

@app.post("/api/pipeline/setup/session")
async def save_setup_session(payload: dict):
    await db.save_advisor_session(payload.get("stage", "idle"), payload.get("data", {}))
    return {"ok": True}

@app.delete("/api/pipeline/setup/session")
async def clear_setup_session():
    await db.clear_advisor_session()
    return {"ok": True}

# ─── NEW: Pipeline — Titles ───────────────────────────────────────────────────

@app.get("/api/pipeline/titles")
async def get_titles():
    return {"titles": await db.get_job_titles()}

@app.post("/api/pipeline/titles")
async def set_titles(request: SetTitlesRequest):
    if not request.titles:
        raise HTTPException(status_code=400, detail="Must provide at least one title.")
    return {"titles": await db.set_job_titles(request.titles)}

@app.post("/api/pipeline/titles/add")
async def add_title(request: AddTitleRequest):
    return {"titles": await db.add_job_title(request.title.strip())}

@app.delete("/api/pipeline/titles/{title_id}")
async def remove_title(title_id: int):
    return {"titles": await db.delete_job_title(title_id)}

# ─── NEW: Pipeline — Run ─────────────────────────────────────────────────────

@app.post("/api/pipeline/run")
async def run_pipeline(request: PipelineRunRequest):
    profile = await db.get_profile()
    if not profile:
        raise HTTPException(status_code=400, detail="No profile saved. Save your profile first.")
    titles = await db.get_job_titles()
    if not titles:
        raise HTTPException(status_code=400, detail="No job titles configured. Complete setup first.")

    intro_text = profile["intro_text"]
    resume_text = profile["resume_text"]
    fetched_total = scored_total = 0
    queued_jobs = []
    errors = []

    for title_row in titles:
        title = title_row["title"]
        result = await adzuna_service.search_jobs(what=title, results_per_page=request.results_per_page, country=request.country)
        if "error" in result:
            errors.append(f"{title}: {result['error']}")
            continue
        jobs = result.get("jobs", [])
        fetched_total += len(jobs)
        for job in jobs:
            scored_total += 1
            try:
                score_result = await pipeline_service.score_job(
                    intro_text=intro_text, resume_text=resume_text,
                    job_title=job["title"], job_description=job.get("description", ""),
                    job_location=job.get("location", ""),
                    themes_text=profile.get("themes_text", ""),
                    locations_preferred=profile.get("locations_preferred", "Remote"),
                    locations_acceptable=profile.get("locations_acceptable", ""),
                    locations_excluded=profile.get("locations_excluded", ""),
                )
            except Exception as e:
                errors.append(f"Scoring '{job['title']}': {str(e)}")
                continue
            score = score_result.get("score", 0)
            if score >= 70:
                job_record = {**job, "score": score, "score_reason": score_result.get("reason", "")}
                await db.upsert_application(job_record)
                queued_jobs.append(job_record)

    return {
        "fetched": fetched_total,
        "scored": scored_total,
        "queued": len(queued_jobs),
        "dropped": scored_total - len(queued_jobs),
        "errors": errors,
        "jobs": sorted(queued_jobs, key=lambda j: j["score"], reverse=True)
    }

# ─── NEW: Pipeline — Queue ────────────────────────────────────────────────────

@app.get("/api/pipeline/queue")
async def get_queue():
    jobs = await db.get_queued_applications()
    return {"jobs": jobs, "count": len(jobs)}

@app.post("/api/pipeline/queue/{job_id}/decide")
async def decide_job(job_id: str, request: DecideRequest):
    if request.action not in ("approve", "reject"):
        raise HTTPException(status_code=400, detail="action must be 'approve' or 'reject'")
    job = await db.update_application_status(job_id, "approved" if request.action == "approve" else "rejected")
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job}

# ─── NEW: Pipeline — Generate ─────────────────────────────────────────────────

@app.post("/api/pipeline/generate/{job_id}")
async def generate_docs(job_id: str):
    profile = await db.get_profile()
    if not profile:
        raise HTTPException(status_code=400, detail="No profile found.")
    job = await db.get_application(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] not in ("approved", "drafted"):
        raise HTTPException(status_code=400, detail="Job must be approved before generating documents.")
    try:
        notes = await pipeline_service.generate_resume_notes(
            intro_text=profile["intro_text"], resume_text=profile["resume_text"],
            job_title=job["title"], job_description=job.get("description", ""),
            themes_text=profile.get("themes_text", ""),
        )
        cover_letter = await pipeline_service.generate_cover_letter(
            intro_text=profile["intro_text"], resume_text=profile["resume_text"],
            job_title=job["title"], company=job["company"],
            job_description=job.get("description", ""),
            themes_text=profile.get("themes_text", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

    resume_notes_text = "\n".join(f"• {n}" for n in notes)
    updated_job = await db.save_generated_docs(job_id, resume_notes_text, cover_letter)
    return {"job": updated_job}

# ─── NEW: Pipeline — Tracker ──────────────────────────────────────────────────

@app.get("/api/pipeline/tracker")
async def get_tracker():
    jobs = await db.get_all_applications()
    return {"jobs": jobs, "count": len(jobs)}

@app.patch("/api/pipeline/tracker/{job_id}/status")
async def update_status(job_id: str, request: UpdateStatusRequest):
    try:
        job = await db.update_application_status(job_id, request.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job}

@app.post("/api/pipeline/tracker/{job_id}/docs")
async def save_docs(job_id: str, request: SaveDocsRequest):
    job = await db.save_generated_docs(job_id, request.resume_notes, request.cover_letter)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job": job}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
