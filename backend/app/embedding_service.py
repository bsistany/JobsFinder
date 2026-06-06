"""
Semantic pre-filter using sentence-transformers (all-MiniLM-L6-v2).
Runs locally — no API key, no data egress, ~90MB model.

Usage in pipeline:
    1. Call embed_profile(intro_text, resume_text) once per run → profile vector
    2. Call is_relevant(job_description, profile_vector, threshold) per job
       → True  = passes to Groq scoring
       → False = dropped before any API call
"""
import logging
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Model loads once at import time — cold start ~5-10s, then cached in memory
_MODEL_NAME = "all-MiniLM-L6-v2"
_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model: %s", _MODEL_NAME)
        _model = SentenceTransformer(_MODEL_NAME)
        logger.info("Model loaded.")
    return _model


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between two 1-D vectors."""
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def embed_profile(intro_text: str, resume_text: str) -> np.ndarray:
    """
    Embed the candidate profile (intro + resume concatenated).
    Called once per pipeline run — result passed to is_relevant() for each job.
    Returns a 384-dim float32 numpy array.
    """
    model = _get_model()
    # Truncate to avoid overwhelming the model — MiniLM handles ~256 tokens well
    combined = f"{intro_text.strip()}\n\n{resume_text.strip()}"
    words = combined.split()
    if len(words) > 400:
        combined = " ".join(words[:400])
    vector = model.encode(combined, convert_to_numpy=True, normalize_embeddings=True)
    logger.info("Profile embedded — vector shape: %s", vector.shape)
    return vector


def embed_job(job_title: str, job_description: str) -> np.ndarray:
    """
    Embed a single job (title + description).
    Returns a 384-dim float32 numpy array.
    """
    model = _get_model()
    combined = f"{job_title.strip()}\n\n{job_description.strip()}"
    words = combined.split()
    if len(words) > 300:
        combined = " ".join(words[:300])
    return model.encode(combined, convert_to_numpy=True, normalize_embeddings=True)


def is_relevant(
    job_title: str,
    job_description: str,
    profile_vector: np.ndarray,
    threshold: float = 0.25,
) -> tuple[bool, float]:
    """
    Returns (passes_filter, similarity_score).
    threshold=0.25 is permissive — tune upward to reduce noise.
    Typical ranges:
        < 0.20 → clearly unrelated
        0.20–0.30 → loosely related
        0.30–0.45 → good domain match
        > 0.45 → strong match
    """
    job_vector = embed_job(job_title, job_description)
    score = _cosine_similarity(profile_vector, job_vector)
    passes = score >= threshold
    return passes, round(score, 4)
