import os
import httpx
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class AdzunaService:
    """Service for interacting with Adzuna Job Search API"""
    
    def __init__(self):
        self.app_id = os.getenv("ADZUNA_APP_ID")
        self.app_key = os.getenv("ADZUNA_APP_KEY")
        self.base_url = "https://api.adzuna.com/v1/api/jobs"
        
        if not self.app_id or not self.app_key:
            print("WARNING: Adzuna credentials not found in environment variables")
    
    async def search_jobs(
        self,
        what: str = "",
        where: str = "",
        country: str = "ca",
        results_per_page: int = 10,
        page: int = 1
    ) -> Dict:
        """
        Search for jobs using Adzuna API
        
        Args:
            what: Job title, keywords, or skills (e.g., "python developer")
            where: Location (e.g., "toronto", "ontario")
            country: Country code (default: "ca" for Canada)
            results_per_page: Number of results (max 50)
            page: Page number
        
        Returns:
            Dictionary with job results and metadata
        """
        if not self.app_id or not self.app_key:
            return {
                "error": "Adzuna API credentials not configured",
                "jobs": [],
                "count": 0
            }
        
        url = f"{self.base_url}/{country}/search/{page}"
        
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "results_per_page": min(results_per_page, 50),
        }
        
        if what:
            params["what"] = what
        if where:
            params["where"] = where
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                # Format the response
                jobs = []
                for job in data.get("results", []):
                    jobs.append({
                        "id": job.get("id"),
                        "title": job.get("title"),
                        "company": job.get("company", {}).get("display_name", "Unknown"),
                        "location": job.get("location", {}).get("display_name", "Unknown"),
                        "description": job.get("description", "")[:500] + "...",  # Truncate
                        "salary_min": job.get("salary_min"),
                        "salary_max": job.get("salary_max"),
                        "contract_type": job.get("contract_type"),
                        "created": job.get("created"),
                        "redirect_url": job.get("redirect_url"),
                        "category": job.get("category", {}).get("label", "Unknown")
                    })
                
                return {
                    "jobs": jobs,
                    "count": data.get("count", 0),
                    "page": page,
                    "results_per_page": results_per_page,
                    "total_pages": (data.get("count", 0) // results_per_page) + 1
                }
                
        except httpx.HTTPStatusError as e:
            return {
                "error": f"Adzuna API error: {e.response.status_code}",
                "jobs": [],
                "count": 0
            }
        except Exception as e:
            return {
                "error": f"Error fetching jobs: {str(e)}",
                "jobs": [],
                "count": 0
            }
    
    async def get_job_categories(self, country: str = "ca") -> List[Dict]:
        """Get available job categories"""
        url = f"{self.base_url}/{country}/categories"
        
        params = {
            "app_id": self.app_id,
            "app_key": self.app_key,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params, timeout=10.0)
                response.raise_for_status()
                return response.json().get("results", [])
        except Exception as e:
            print(f"Error fetching categories: {e}")
            return []

# Create singleton instance
adzuna_service = AdzunaService()
