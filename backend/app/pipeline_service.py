import os
import re
import json
import logging
from groq import Groq
from typing import List, Dict
from dotenv import load_dotenv
from app.location import extract_city, is_preferred, is_acceptable, is_excluded

logger = logging.getLogger(__name__)

load_dotenv()
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
        intro_trunc = _truncate(intro_text, 200)
        resume_trunc = _truncate(resume_text, 300)

        prompt = f"""You are a career advisor helping a professional find the best-fit job roles.
Analyze the intro document and resume below, then:
1. Summarize the candidate's background
2. Suggest 8-12 specific job search titles that would match their profile — vary across:
   - function variants (engineering, architecture, consulting, advisory)
   - industry angles (product security, compliance, governance, risk)
   - role types (individual contributor, management, leadership)
   IMPORTANT: Do NOT include seniority qualifiers (Senior, Principal, Director, VP, Head of, Lead) in the titles.
   Use only the core title (e.g. "Application Security Engineer" not "Senior Application Security Engineer").
   Seniority is handled separately at the scoring stage.
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
    {{ "title": "Core Job Title Without Seniority", "rationale": "one sentence why this fits" }}
  ],
  "questions": [
    {{ "id": "q1", "text": "First clarifying question" }},
    {{ "id": "q2", "text": "Second clarifying question" }},
    {{ "id": "q3", "text": "Third clarifying question" }}
  ]
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = _strip_json_fences(response.choices[0].message.content)
        # If response was truncated, attempt to salvage partial JSON
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Truncate to last complete top-level field and close the object
            last_brace = raw.rfind('},')
            if last_brace > 0:
                raw = raw[:last_brace + 1] + ']}'
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

Titles the candidate has already selected and confirmed:
{json.dumps(suggested_titles, indent=2)}

Clarifying answers:
{json.dumps(answers, indent=2)}

IMPORTANT: Keep ALL of the already-selected titles above — do not remove any of them.
Based on the clarifying answers, you may ADD up to 3 additional titles if the answers
suggest relevant directions not already covered. Do not add titles that overlap with
existing ones.

Respond with JSON only:
{{
  "titles": ["Every selected title preserved, plus any new additions"],
  "summary": "One sentence confirming what you set up and why"
}}"""

        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = _strip_json_fences(response.choices[0].message.content)
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            titles = re.findall(r'"([^"]+)"', raw.split('"titles"')[-1])
            return {"titles": [t for t in titles if len(t) < 80 and t.lower() != 'summary'], "summary": "Titles extracted from partial response."}
        # Guard: ensure titles is a flat list of short strings only
        titles = result.get("titles", [])
        titles = [t for t in titles if isinstance(t, str) and len(t) < 80 and t.lower() != 'summary']
        result["titles"] = titles
        return result

    # ─── Scoring ──────────────────────────────────────────────────────────────

    async def score_job(
        self,
        intro_text: str,
        resume_text: str,
        job_title: str,
        job_description: str,
        job_location: str = '',
        location_tier: str = 'preferred',
        themes_text: str = '',
    ) -> dict:
        """
        Score a single job against the user's profile.
        Location exclusion is handled before this call in Python — only
        preferred/acceptable jobs reach here. The acceptable penalty (-5)
        is applied deterministically in Python after scoring.
        Truncation: intro ≤180w, resume ≤350w, JD ≤280w, themes ≤80w.

        Returns: { "score": int 0-100, "reason": str ≤20 words }
        """
        intro_trunc = _truncate(intro_text, 180)
        resume_trunc = _truncate(resume_text, 350)
        jd_trunc = _truncate(job_description, 280)
        themes_trunc = _truncate(themes_text, 80) if themes_text.strip() else ''
        themes_block = f"\nCandidate career narrative:\n{themes_trunc}" if themes_trunc else ''

        location_note = (
            f"Location: {job_location} (preferred)"
            if location_tier == "preferred"
            else f"Location: {job_location} (acceptable — candidate open to this location)"
        )

        prompt = f"""Score how well this job matches the candidate. Return JSON only.

Candidate intro:
{intro_trunc}

Candidate resume:
{resume_trunc}{themes_block}

Job title: {job_title}
{location_note}
Job description:
{jd_trunc}

Scoring criteria (total 100):
- Skills match (40%): how well candidate skills match JD requirements
- Experience level (30%): seniority and years align
- Role alignment (30%): matches candidate's target per their intro

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
        try:
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error("score_job JSON parse failed for '%s': %s | raw: %s", job_title, e, raw[:200])
            raise

        # Apply acceptable penalty deterministically — not left to Groq
        score = max(0, min(100, int(result["score"])))
        if location_tier == "acceptable":
            score = max(0, score - 5)
        result["score"] = score
        return result

    # ─── Document generation ──────────────────────────────────────────────────

    async def generate_resume_notes(
        self,
        intro_text: str,
        resume_text: str,
        job_title: str,
        job_description: str,
        themes_text: str = '',
    ) -> list[str]:
        """
        Generate 5 bullet points to tailor the user's resume for this specific job.
        Returns a list of strings.
        """
        intro_trunc = _truncate(intro_text, 200)
        resume_trunc = _truncate(resume_text, 400)
        jd_trunc = _truncate(job_description, 400)
        themes_trunc = _truncate(themes_text, 100) if themes_text.strip() else ''
        themes_block = f"\nCareer narrative (emphasis patterns to preserve):\n{themes_trunc}" if themes_trunc else ''

        prompt = f"""You are a professional resume coach. Generate specific, actionable bullet points
to help the candidate tailor their resume for this job.

Candidate intro:
{intro_trunc}

Candidate resume:
{resume_trunc}{themes_block}

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
        job_description: str,
        themes_text: str = '',
    ) -> str:
        """
        Generate a tailored cover letter draft. Returns plain text.
        """
        intro_trunc = _truncate(intro_text, 200)
        resume_trunc = _truncate(resume_text, 400)
        jd_trunc = _truncate(job_description, 400)
        themes_trunc = _truncate(themes_text, 120) if themes_text.strip() else ''
        themes_block = f"\nCareer narrative (mirror this voice, tone and emphasis in the letter):\n{themes_trunc}" if themes_trunc else ''

        prompt = f"""Write a tailored professional cover letter for this job application.

Candidate intro:
{intro_trunc}

Candidate resume:
{resume_trunc}{themes_block}

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
