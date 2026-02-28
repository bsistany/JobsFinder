import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()

class ClaudeService:
    """Service for using Claude to parse natural language job search queries."""

    def __init__(self):
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("WARNING: ANTHROPIC_API_KEY not found in environment variables")
        self.client = anthropic.Anthropic(api_key=api_key)

    async def parse_job_search_query(self, user_message: str) -> dict:
        """
        Use Claude to extract structured job search parameters from natural language.

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

        message = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = message.content[0].text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        return json.loads(raw)


# Singleton instance
claude_service = ClaudeService()
