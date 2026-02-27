from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from app.adzuna_service import adzuna_service

app = FastAPI(title="Job Search AI API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class ChatMessage(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

class JobSearchQuery(BaseModel):
    what: Optional[str] = ""
    where: Optional[str] = ""
    page: Optional[int] = 1
    results_per_page: Optional[int] = 10

# Routes
@app.get("/")
async def root():
    return {
        "message": "Job Search AI API",
        "status": "running",
        "version": "0.2.0",
        "features": ["chat", "job_search", "adzuna_integration"]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(message: ChatMessage):
    """
    Handle chat messages from the frontend.
    This is where you'll integrate Claude API later for natural language processing.
    """
    # Simple keyword detection for now
    msg = message.message.lower()
    
    if any(word in msg for word in ["job", "find", "search", "looking for"]):
        return ChatResponse(
            response="I can help you search for jobs! Try using the format: 'Find [job title] jobs in [location]'. For example: 'Find Python developer jobs in Toronto'"
        )
    elif any(word in msg for word in ["cover letter", "resume", "cv"]):
        return ChatResponse(
            response="Cover letter and resume features are coming in Phase 3 with AI integration!"
        )
    else:
        return ChatResponse(
            response=f"You said: {message.message}. I'm still learning! Try asking me to find jobs or help with cover letters."
        )

@app.get("/api/jobs/search")
async def search_jobs(
    what: str = "",
    where: str = "",
    page: int = 1,
    results_per_page: int = 10
):
    """
    Search for jobs using Adzuna API.
    
    Query parameters:
    - what: Job title, keywords, or skills (e.g., "python developer")
    - where: Location (e.g., "toronto", "ontario")
    - page: Page number (default: 1)
    - results_per_page: Results per page (default: 10, max: 50)
    """
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
    """
    Search for jobs using POST (for complex queries).
    """
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
    """
    Get available job categories from Adzuna.
    """
    categories = await adzuna_service.get_job_categories()
    return {"categories": categories}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
