import os
import json
from groq import Groq
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

# Word-count based truncation — keeps prompts token-safe
def _truncate(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"

def _strip_json_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


class PipelineService:
    """
    All Groq/LLM calls for the personal job match pipeline.
    Keeps the original ClaudeService in claude_service.py untouched
    so the existing Career Advisor tab continues to work.
    """

    def __init__(self):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("WARNING: GROQ_API_KEY not found in environment variables")
        self.client = Groq(api_key=api_key)
        self.model = "llama-3.1-8b-instant"

    # ─── Career Advisor (pipeline setup) ─────────────────────────────────────

    async def analyze_profile(self, intro_text: str, resume_text: str) -> dict:
        """
        Analyze the user's intro doc + resume and return a candidate profile
        plus suggested job search titles.

        Returns:
        {
            "profile": {
                "summary": str,
                "experience_level": str,
                "key_skills": [str],
            },
            "suggested_titles": [
                { "title": str, "rationale": str }
            ],
            "questions": [
                { "id": str, "text": str }
            ]
        }
        """
        intro_trunc = _truncate(intro_text, 300)
        resume_trunc = _truncate(resume_text, 400)

        prompt = f"""You are a career advisor helping a professional find the best-fit job roles.
Analyze the intro document and resume below, then:
1. Summarize the candidate's background
2. Suggest 8-12 specific job search titles that would match their profile — vary across:
   - seniority levels (senior, principal, director, VP, head of)
   - function variants (engineering, architecture, consulting, advisory)
   - industry angles (product security, compliance, governance, risk)
3. Ask 2-3 clarifying questions to refine the titles (location preference, role type, industry focus, IC vs management)

Intro document:
{intro_trunc}

Resume:
{resume_trunc}

Respond with JSON only, no explanation. Use this exact structure:
{{
  "profile": {{
    "summary": "2-sentence summary of candidate background",
    "experience_level": "junior or mid or senior or executive",
    "key_skills": ["up to 8 most relevant skills"]
  }},
  "suggested_titles": [
    {{ "title": "Exact Job Title To Search", "rationale": "one sentence why this fits" }}
  ],
  "questions": [
    {{ "id": "q1", "text": "First clarifying question" }},
    {{ "id": "q2", "text": "Second clarifying question" }},
    {{ "id": "q3", "text": "Third clarifying question" }}
  ]
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = _strip_json_fences(response.choices[0].message.content)
        return json.loads(raw)

    async def refine_titles(
        self,
        profile: dict,
        suggested_titles: list,
        answers: List[Dict]
    ) -> dict:
        """
        Given the initial profile + suggested titles + user's Q&A answers,
        produce the final confirmed list of job titles to store.

        Returns:
        {
            "titles": ["Title 1", "Title 2", ...],
            "summary": "one sentence confirming what was set up"
        }
        """
        prompt = f"""You are a career advisor finalizing a job search setup.

Candidate profile:
{json.dumps(profile, indent=2)}

Initially suggested titles:
{json.dumps(suggested_titles, indent=2)}

Clarifying answers:
{json.dumps(answers, indent=2)}

Based on the answers, produce the final list of job search titles to use.
Keep titles that still fit, remove any that don't match the preferences expressed,
and add new ones if the answers suggest better directions.

Respond with JSON only:
{{
  "titles": ["Final Title 1", "Final Title 2", "...up to 6 titles"],
  "summary": "One sentence confirming what you set up and why"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = _strip_json_fences(response.choices[0].message.content)
        return json.loads(raw)

    # ─── Scoring ──────────────────────────────────────────────────────────────

    async def score_job(
        self,
        intro_text: str,
        resume_text: str,
        job_title: str,
        job_description: str
    ) -> dict:
        """
        Score a single job against the user's profile.
        Kept lean: intro ≤200w, resume ≤400w, JD ≤300w → stays under 1000 tokens.

        Returns: { "score": int 0-100, "reason": str ≤20 words }
        """
        intro_trunc = _truncate(intro_text, 200)
        resume_trunc = _truncate(resume_text, 400)
        jd_trunc = _truncate(job_description, 300)

        prompt = f"""Score how well this job matches the candidate. Return JSON only.

Candidate intro:
{intro_trunc}

Candidate resume summary:
{resume_trunc}

Job title: {job_title}
Job description:
{jd_trunc}

Scoring criteria:
- Skills match (40%): how well candidate's skills match the JD requirements
- Experience level match (30%): seniority and years align
- Role alignment (30%): matches what candidate is targeting per their intro

Return JSON only, no explanation:
{{
  "score": <integer 0-100>,
  "reason": "<one sentence, max 20 words, explaining the key match or gap>"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=80,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = _strip_json_fences(response.choices[0].message.content)
        result = json.loads(raw)
        result["score"] = max(0, min(100, int(result["score"])))
        return result

    # ─── Document generation ──────────────────────────────────────────────────

    async def generate_resume_notes(
        self,
        intro_text: str,
        resume_text: str,
        job_title: str,
        job_description: str
    ) -> list[str]:
        """
        Generate 5 bullet points to tailor the user's resume for this specific job.
        Returns a list of strings.
        """
        intro_trunc = _truncate(intro_text, 200)
        resume_trunc = _truncate(resume_text, 400)
        jd_trunc = _truncate(job_description, 400)

        prompt = f"""You are a professional resume coach. Generate specific, actionable bullet points
to help the candidate tailor their resume for this job.

Candidate intro:
{intro_trunc}

Candidate resume:
{resume_trunc}

Target job: {job_title}
Job description:
{jd_trunc}

Return JSON only:
{{
  "notes": [
    "Specific bullet point 1 — what to add, emphasize, or reword",
    "Specific bullet point 2",
    "Specific bullet point 3",
    "Specific bullet point 4",
    "Specific bullet point 5"
  ]
}}

Make each note concrete and actionable — reference specific skills or experiences from their background
and connect them to specific requirements in the JD."""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = _strip_json_fences(response.choices[0].message.content)
        result = json.loads(raw)
        return result.get("notes", [])

    async def generate_cover_letter(
        self,
        intro_text: str,
        resume_text: str,
        job_title: str,
        company: str,
        job_description: str
    ) -> str:
        """
        Generate a tailored cover letter draft. Returns plain text.
        """
        intro_trunc = _truncate(intro_text, 200)
        resume_trunc = _truncate(resume_text, 400)
        jd_trunc = _truncate(job_description, 400)

        prompt = f"""Write a tailored professional cover letter for this job application.

Candidate intro:
{intro_trunc}

Candidate resume:
{resume_trunc}

Job title: {job_title}
Company: {company}
Job description:
{jd_trunc}

Write 3 paragraphs:
1. Opening — specific hook connecting candidate's background to this role and company
2. Middle — 2-3 concrete achievements/skills from their background that directly address JD requirements
3. Closing — enthusiasm, call to action, professional sign-off

Use plain text. No placeholders like [Your Name] — write the letter as if complete.
Address to "Hiring Manager" if no contact name is available.
Keep it under 350 words. Do not include a date line or address block."""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()


# Singleton
pipeline_service = PipelineService()
