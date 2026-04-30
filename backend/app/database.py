import os
import aiosqlite
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database/job_search.db")
DB_PATH = DATABASE_URL.replace("sqlite:///", "")

CREATE_PROFILE_TABLE = """
CREATE TABLE IF NOT EXISTS profile (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    intro_text TEXT NOT NULL DEFAULT '',
    resume_text TEXT NOT NULL DEFAULT '',
    themes_text TEXT NOT NULL DEFAULT '',
    locations_preferred TEXT NOT NULL DEFAULT 'Remote',
    locations_acceptable TEXT NOT NULL DEFAULT '',
    locations_excluded TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

MIGRATE_PROFILE_V2 = [
    "ALTER TABLE profile ADD COLUMN themes_text TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE profile ADD COLUMN locations_preferred TEXT NOT NULL DEFAULT 'Remote'",
    "ALTER TABLE profile ADD COLUMN locations_acceptable TEXT NOT NULL DEFAULT ''",
    "ALTER TABLE profile ADD COLUMN locations_excluded TEXT NOT NULL DEFAULT ''",
]

CREATE_JOB_TITLES_TABLE = """
CREATE TABLE IF NOT EXISTS job_titles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL UNIQUE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_APPLICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS applications (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT,
    description TEXT,
    salary_min REAL,
    salary_max REAL,
    redirect_url TEXT,
    score INTEGER NOT NULL,
    score_reason TEXT,
    status TEXT NOT NULL DEFAULT 'queued',
    resume_notes TEXT,
    cover_letter TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

CREATE_PIPELINE_RUNS_TABLE = """
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    fetched INTEGER NOT NULL DEFAULT 0,
    location_excluded INTEGER NOT NULL DEFAULT 0,
    scored INTEGER NOT NULL DEFAULT 0,
    queued INTEGER NOT NULL DEFAULT 0,
    dropped INTEGER NOT NULL DEFAULT 0
)
"""

MIGRATE_APPLICATIONS_V2 = [
    "ALTER TABLE applications ADD COLUMN fetched_at TIMESTAMP",
    "UPDATE applications SET fetched_at = CURRENT_TIMESTAMP WHERE fetched_at IS NULL",
]

CREATE_ADVISOR_SESSION_TABLE = """
CREATE TABLE IF NOT EXISTS advisor_session (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    stage TEXT NOT NULL DEFAULT 'idle',
    data TEXT NOT NULL DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

async def _connect() -> aiosqlite.Connection:
    """Open a connection, set row_factory and WAL mode. Always use as async with."""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    return db

async def init_db():
    import os as _os
    _os.makedirs(_os.path.dirname(DB_PATH) if _os.path.dirname(DB_PATH) else ".", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(CREATE_PROFILE_TABLE)
        await db.execute(CREATE_JOB_TITLES_TABLE)
        await db.execute(CREATE_APPLICATIONS_TABLE)
        await db.execute(CREATE_ADVISOR_SESSION_TABLE)
        await db.execute(CREATE_PIPELINE_RUNS_TABLE)
        # v0.7.0 — profile columns
        for sql in MIGRATE_PROFILE_V2:
            try:
                await db.execute(sql)
            except Exception:
                pass
        # v0.8.0 — applications fetched_at column + backfill
        for sql in MIGRATE_APPLICATIONS_V2:
            try:
                await db.execute(sql)
            except Exception:
                pass
        await db.commit()

# ─── Profile helpers ─────────────────────────────────────────────────────────

async def get_profile() -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM profile WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def upsert_profile(
    intro_text: str,
    resume_text: str,
    themes_text: str = '',
    locations_preferred: str = 'Remote',
    locations_acceptable: str = '',
    locations_excluded: str = '',
) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
            INSERT INTO profile (id, intro_text, resume_text, themes_text,
                locations_preferred, locations_acceptable, locations_excluded, updated_at)
            VALUES (1, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                intro_text = excluded.intro_text,
                resume_text = excluded.resume_text,
                themes_text = excluded.themes_text,
                locations_preferred = excluded.locations_preferred,
                locations_acceptable = excluded.locations_acceptable,
                locations_excluded = excluded.locations_excluded,
                updated_at = CURRENT_TIMESTAMP
        """, (intro_text, resume_text, themes_text,
              locations_preferred, locations_acceptable, locations_excluded))
        await db.commit()
    return await get_profile()

# ─── Job title helpers ────────────────────────────────────────────────────────

async def get_job_titles() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM job_titles ORDER BY added_at DESC") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def set_job_titles(titles: list[str]) -> list[dict]:
    """Replace all job titles with the provided list."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("DELETE FROM job_titles")
        for title in titles:
            await db.execute(
                "INSERT OR IGNORE INTO job_titles (title) VALUES (?)", (title,)
            )
        await db.commit()
    return await get_job_titles()

async def add_job_title(title: str) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(
            "INSERT OR IGNORE INTO job_titles (title) VALUES (?)", (title,)
        )
        await db.commit()
    return await get_job_titles()

async def delete_job_title(title_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("DELETE FROM job_titles WHERE id = ?", (title_id,))
        await db.commit()
    return await get_job_titles()

# ─── Application helpers ──────────────────────────────────────────────────────

async def upsert_application(job: dict) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
            INSERT INTO applications
                (id, title, company, location, description,
                 salary_min, salary_max, redirect_url,
                 score, score_reason, status, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO NOTHING
        """, (
            job["id"], job["title"], job["company"], job["location"],
            job["description"], job.get("salary_min"), job.get("salary_max"),
            job.get("redirect_url"), job["score"], job["score_reason"]
        ))
        await db.commit()

async def get_queued_applications() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM applications WHERE status = 'queued' ORDER BY score DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_all_applications() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM applications ORDER BY score DESC, created_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

async def get_application(job_id: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM applications WHERE id = ?", (job_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_application_status(job_id: str, status: str) -> dict | None:
    valid = {"queued", "approved", "rejected", "drafted", "applied", "no_response"}
    if status not in valid:
        raise ValueError(f"Invalid status: {status}")
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
            UPDATE applications
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, job_id))
        await db.commit()
    return await get_application(job_id)

async def save_generated_docs(job_id: str, resume_notes: str, cover_letter: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
            UPDATE applications
            SET resume_notes = ?, cover_letter = ?, status = 'drafted',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (resume_notes, cover_letter, job_id))
        await db.commit()
    return await get_application(job_id)

# ─── Advisor session helpers ──────────────────────────────────────────────────

async def get_advisor_session() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM advisor_session WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if not row:
                return {"stage": "idle", "data": {}}
            import json
            return {"stage": row["stage"], "data": json.loads(row["data"])}

async def save_advisor_session(stage: str, data: dict) -> None:
    import json
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
            INSERT INTO advisor_session (id, stage, data, updated_at)
            VALUES (1, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                stage = excluded.stage,
                data = excluded.data,
                updated_at = CURRENT_TIMESTAMP
        """, (stage, json.dumps(data)))
        await db.commit()

async def clear_advisor_session() -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM advisor_session WHERE id = 1")
        await db.commit()

# ─── Pipeline run helpers ─────────────────────────────────────────────────────

async def log_pipeline_run(
    fetched: int,
    location_excluded: int,
    scored: int,
    queued: int,
    dropped: int,
) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO pipeline_runs
                (fetched, location_excluded, scored, queued, dropped)
            VALUES (?, ?, ?, ?, ?)
        """, (fetched, location_excluded, scored, queued, dropped))
        await db.commit()

async def get_last_pipeline_run() -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM pipeline_runs ORDER BY run_at DESC LIMIT 1"
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def clear_queue() -> int:
    """Delete all queued applications. Returns count deleted."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT COUNT(*) as cnt FROM applications WHERE status = 'queued'"
        ) as cursor:
            row = await cursor.fetchone()
            count = row["cnt"] if row else 0
        await db.execute("DELETE FROM applications WHERE status = 'queued'")
        await db.commit()
    return count
