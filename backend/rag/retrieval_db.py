from functools import lru_cache
import heapq
from pathlib import Path
import re

import pandas as pd

from backend.database.models import fetch_all_resumes


ROOT_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = ROOT_DIR / "dataset" / "Resume" / "Resume.csv"

CATEGORY_ALIASES = {
    "information technology": {"it", "software", "developer", "python", "backend", "programmer"},
    "business development": {"sales", "lead generation", "client acquisition", "growth"},
    "digital media": {"seo", "social media", "content", "marketing"},
    "public relations": {"communications", "media relations", "branding"},
    "hr": {"recruitment", "human resources", "talent acquisition"},
}


def _normalize(text: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def _tokenize(text: str) -> list[str]:
    normalized = _normalize(text)
    return [token for token in normalized.split(" ") if token]


@lru_cache(maxsize=1)
def _load_category_lookup():
    df = pd.read_csv(CSV_PATH)
    text_to_category = dict(zip(df["Resume_str"], df["Category"]))
    categories = sorted(df["Category"].unique())
    normalized_categories = {_normalize(category): category for category in categories}
    return text_to_category, categories, normalized_categories


def _keyword_score(query: str, text: str) -> int:
    query_words = _tokenize(query)
    text_lower = _normalize(text)

    score = 0
    for word in query_words:
        score += text_lower.count(word)

    return score


def _category_similarity(query: str, category: str) -> float:
    query_norm = _normalize(query)
    category_norm = _normalize(category)

    if not query_norm or not category_norm:
        return 0.0

    if query_norm == category_norm:
        return 1.0

    query_tokens = set(_tokenize(query_norm))
    category_tokens = set(_tokenize(category_norm))

    if not query_tokens or not category_tokens:
        return 0.0

    overlap = len(query_tokens & category_tokens) / len(category_tokens)

    alias_boost = 0.0
    aliases = CATEGORY_ALIASES.get(category_norm, set())
    if any(alias in query_norm for alias in aliases):
        alias_boost = 0.55

    partial_phrase = 0.35 if category_norm in query_norm or query_norm in category_norm else 0.0

    return max(overlap, alias_boost, partial_phrase)


def _resolve_category(text: str):
    text_to_category, _, _ = _load_category_lookup()
    return text_to_category.get(text)


def _rank_score(query: str, text: str, category: str | None) -> float:
    keyword = _keyword_score(query, text)
    category_sim = _category_similarity(query, category) if category else 0.0

    exact_query_match = 1.0 if _normalize(query) in _normalize(text) else 0.0

    return (category_sim * 1000.0) + (exact_query_match * 150.0) + (keyword * 5.0)


def retrieve_candidates(query, limit=25):
    resumes = fetch_all_resumes()

    top_ranked = heapq.nlargest(
        limit,
        resumes,
        key=lambda row: _rank_score(query, row[1], _resolve_category(row[1])),
    )

    return {
        "ids": [[str(row[0]) for row in top_ranked]],
        "documents": [[row[1] for row in top_ranked]],
    }
