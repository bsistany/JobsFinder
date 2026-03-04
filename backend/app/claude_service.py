import os
import json
from groq import Groq
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

class ClaudeService:
    """Service for using Groq (LLaMA) for all AI/NLP tasks."""

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("WARNING: GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"

    # ─── Job Search ───────────────────────────────────────────────────────────

    async def parse_job_search_query(self, user_message: str) -> dict:
        """
        Parse natural language into structured job search parameters.
        Returns: { is_job_search, what, where }
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

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)

    async def format_job_results(self, what: str, where: str, jobs: List[Dict], total_count: int) -> str:
        """
        Generate a natural conversational summary of job search results.
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

    # ─── Career Advisor ───────────────────────────────────────────────────────

    async def analyze_resume(self, resume_text: str) -> dict:
        """
        Analyze a resume and return a candidate profile + clarifying questions.

        Returns:
        {
            "profile": {
                "summary": "brief summary of candidate",
                "experience_level": "senior / mid / junior",
                "key_skills": ["skill1", "skill2", ...],
                "possible_directions": ["direction1", "direction2", ...]
            },
            "questions": [
                { "id": "q1", "text": "question text" },
                ...
            ]
        }
        """
        prompt = f"""You are a career advisor. Analyze the following resume and return a structured JSON response.

Resume:
{resume_text}

Respond with a JSON object only, no explanation. Use this exact structure:
{{
  "profile": {{
    "summary": "2-sentence summary of the candidate's background",
    "experience_level": "junior or mid or senior or executive",
    "key_skills": ["up to 8 most relevant skills"],
    "possible_directions": ["3-5 job directions this person could pursue based on their background"]
  }},
  "questions": [
    {{ "id": "q1", "text": "First clarifying question" }},
    {{ "id": "q2", "text": "Second clarifying question" }},
    {{ "id": "q3", "text": "Third clarifying question" }}
  ]
}}

Rules for questions:
- Ask about role type preference (e.g. individual contributor vs management/leadership)
- Ask about location preference (remote, hybrid, on-site, specific city)
- Ask about one other relevant preference based on their background (e.g. industry, company size, contract vs permanent)
- Keep questions short and conversational
- Do not ask for information already clearly stated in the resume"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)

    async def suggest_job_titles(self, profile: dict, answers: List[Dict]) -> dict:
        """
        Based on resume profile and clarifying answers, suggest job titles to search for.

        Args:
            profile: the profile dict returned by analyze_resume
            answers: list of { "question_id": "q1", "question": "...", "answer": "..." }

        Returns:
        {
            "searches": [
                { "title": "Senior Security Manager", "rationale": "why this fits" },
                ...
            ],
            "intro": "conversational intro message to show the user"
        }
        """
        prompt = f"""You are a career advisor. Based on a candidate's profile and their answers to clarifying questions,
suggest the best job titles to search for.

Candidate profile:
{json.dumps(profile, indent=2)}

Clarifying question answers:
{json.dumps(answers, indent=2)}

Respond with a JSON object only, no explanation. Use this exact structure:
{{
  "intro": "A warm 2-sentence message summarizing what you understood and what you're going to search for",
  "searches": [
    {{ "title": "Job Title To Search", "rationale": "one sentence why this fits the candidate" }},
    {{ "title": "Another Job Title", "rationale": "one sentence why this fits" }}
  ]
}}

Rules:
- Suggest 3-5 distinct job titles that reflect the candidate's possible directions and their answers
- Titles should be specific enough to return good Adzuna search results (e.g. "Security Manager" not just "Manager")
- Reflect both breadth (different directions) and the preferences expressed in their answers
- Keep the intro friendly and specific to this candidate"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.choices[0].message.content.strip()

        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)


# Singleton instance
claude_service = ClaudeService()
