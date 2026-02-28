import os
import json
from groq import Groq
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class ClaudeService:
    """Service for using Groq (LLaMA) to parse natural language job search queries."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("WARNING: GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"

    async def parse_job_search_query(self, user_message: str) -> dict:
        """
        Use LLaMA via Groq to extract structured job search parameters from natural language.

        Returns a dict with:
        - is_job_search (bool): whether the message is a job search request
        - what (str): job title / keywords
        - where (str): location
        """
        prompt = f"""You are a job search assistant. Analyze the user's message and extract job search parameters.

User message: "{user_message}"

Respond with a JSON object only, no explanation. Use this exact structure:
{{
  "is_job_search": true or false,
  "what": "job title or keywords, empty string if not specified",
  "where": "location, empty string if not specified"
}}

Rules:
- Set is_job_search to true if the user is looking for jobs, roles, positions, or work
- For "what", extract the job title or skills (e.g. "senior cybersecurity engineer", "React developer")
- For "where", extract the location (e.g. "Toronto", "remote", "Ontario")
- If location is "remote" or "work from home", set where to "remote"
- If no location is mentioned, leave where as empty string"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)

    async def format_job_results(self, what: str, where: str, jobs: List[Dict], total_count: int) -> str:
        """
        Use LLaMA via Groq to generate a natural conversational summary of job search results.

        Args:
            what: Job title / keywords searched
            where: Location searched
            jobs: List of job results
            total_count: Total number of results found

        Returns:
            A conversational summary string
        """
        job_summaries = [
            {
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
            }
            for job in jobs[:10]
        ]

        prompt = f"""You are a friendly job search assistant. A user searched for jobs and got results.
Write a brief, natural, conversational summary of what was found (2-3 sentences max).
Mention the total count, highlight anything interesting like salary ranges or variety of companies.
Do not list all the jobs — just give a helpful overview. End with a light encouragement.

Search: "{what}" in "{where if where else 'any location'}"
Total results found: {total_count}
Top results: {json.dumps(job_summaries, indent=2)}"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content.strip()


# Singleton instance
claude_service = ClaudeService()
