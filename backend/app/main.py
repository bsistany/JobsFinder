from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from app.adzuna_service import adzuna_service
from app.claude_service import claude_service

app = FastAPI(title="Job Search AI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Models ──────────────────────────────────────────────────────────────────

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

# ─── General Routes ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "message": "Job Search AI API",
        "status": "running",
        "version": "0.5.0",
        "features": ["chat", "job_search", "adzuna_integration", "claude_nlp", "claude_responses", "career_advisor"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ─── Job Search Routes ────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Handle chat messages using Claude for natural language understanding and response generation.
    """
    try:
        parsed = await claude_service.parse_job_search_query(message.message)
    except Exception as e:
        return ChatResponse(response=f"Sorry, I had trouble understanding that. Could you rephrase? (Error: {str(e)})")

    if not parsed.get("is_job_search"):
        return ChatResponse(
            response="I'm your job search assistant! Try asking me something like: 'Find senior cybersecurity jobs in remote' or 'Show me React developer roles in Toronto'."
        )

    what = parsed.get("what", "")
    where = parsed.get("where", "")

    result = await adzuna_service.search_jobs(
        what=what,
        where=where,
        results_per_page=10
    )

    if "error" in result:
        return ChatResponse(response=f"I understood your search but ran into an issue fetching results: {result['error']}")

    jobs = result.get("jobs", [])
    count = result.get("count", 0)

    if not jobs:
        return ChatResponse(
            response=f"I searched for '{what}'{' in ' + where if where else ''} but found no results. Try broader keywords or a different location."
        )

    try:
        summary = await claude_service.format_job_results(
            what=what,
            where=where,
            jobs=jobs,
            total_count=count
        )
    except Exception:
        summary = f"Found {count} jobs for \"{what}\"{' in ' + where if where else ''}. Here are the top results:"

    return ChatResponse(response=summary, jobs=jobs, job_count=count)

@app.get("/api/jobs/search")
async def search_jobs(
    what: str = "",
    where: str = "",
    page: int = 1,
    results_per_page: int = 10
):
    result = await adzuna_service.search_jobs(
        what=what,
        where=where,
        page=page,
        results_per_page=results_per_page
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.post("/api/jobs/search")
async def search_jobs_post(query: JobSearchQuery):
    result = await adzuna_service.search_jobs(
        what=query.what,
        where=query.where,
        page=query.page,
        results_per_page=query.results_per_page
    )
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@app.get("/api/jobs/categories")
async def get_categories():
    categories = await adzuna_service.get_job_categories()
    return {"categories": categories}

# ─── Career Advisor Routes ────────────────────────────────────────────────────

@app.post("/api/advisor/analyze")
async def analyze_resume(request: ResumeAnalysisRequest):
    """
    Analyze a resume and return a candidate profile + clarifying questions.
    """
    if not request.resume_text or len(request.resume_text.strip()) < 100:
        raise HTTPException(status_code=400, detail="Resume text is too short.")

    try:
        result = await claude_service.analyze_resume(request.resume_text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing resume: {str(e)}")

@app.post("/api/advisor/suggest")
async def suggest_jobs(request: JobSuggestionsRequest):
    """
    Based on resume profile + clarifying answers, suggest job titles to search for.
    """
    try:
        answers = [a.dict() for a in request.answers]
        result = await claude_service.suggest_job_titles(
            profile=request.profile,
            answers=answers
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error suggesting jobs: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
