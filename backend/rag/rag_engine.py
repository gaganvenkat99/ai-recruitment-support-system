import re
from typing import List, Optional
from datetime import datetime
from functools import lru_cache

from backend.database.models import fetch_all_resumes
from backend.rag.retrieval_db import retrieve_candidates
from sentence_transformers import SentenceTransformer, util
from backend.llm.llm_service import generate_llm_insights, llm_is_configured

# 🔥 Load model once
def _load_embedding_model():
    model_name = "sentence-transformers/all-mpnet-base-v2"
    try:
        return SentenceTransformer(model_name, local_files_only=True)
    except Exception:
        return SentenceTransformer(model_name)


_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = _load_embedding_model()
    return _MODEL

SOFT_SKILL_KEYWORDS = {
    "communication", "leadership", "management", "presentation", "problem solving",
    "teamwork", "microsoft word", "microsoft excel", "powerpoint", "ms word",
    "ms excel", "excel", "word", "power bi", "sql", "python", "java", "c",
    "c++", "c#", "javascript", "typescript", "react", "django", "flask",
    "fastapi", "html", "css", "machine learning", "data analysis",
}

ROLE_HINTS = {
    "python": {"python", "django", "flask", "fastapi", "backend", "developer", "programmer"},
    "developer": {"developer", "programmer", "software", "backend", "engineer"},
    "data": {"data", "analytics", "reporting", "sql", "bi", "power bi", "etl"},
    "analyst": {"analyst", "analysis", "analytics", "reporting", "bi", "power bi", "tableau"},
    "java": {"java", "spring", "backend", "developer"},
    "frontend": {"frontend", "react", "angular", "javascript", "typescript", "ui"},
    "hr": {"hr", "recruitment", "talent", "human resources"},
}

NON_NAME_TOKENS = {
    "developer", "engineer", "manager", "analyst", "consultant", "specialist", "administrator",
    "director", "officer", "architect", "lead", "intern", "technology", "information", "data",
    "senior", "junior", "executive", "profile", "summary", "objective", "experience", "skills",
    "professional", "curriculum", "vitae", "resume", "aws", "drupal", "database", "master",
}

SECTION_HEADINGS = [
    "summary", "professional summary", "profile", "professional profile", "objective",
    "experience", "work experience", "employment history", "education", "skills",
    "technical skills", "projects", "certifications", "achievements", "strengths",
]

MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10,
    "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}


def _looks_like_binary_or_broken_text(text):

    if not text:
        return True

    sample = text[:200].lower()
    broken_markers = [
        "%pdf-",
        "endobj",
        "/type/catalog",
        "xref",
        "stream",
    ]

    return any(marker in sample for marker in broken_markers)


def calculate_match_score(query, text):

    if not query or not text:
        return 0.0

    text = text[:500]

    model = _get_model()
    emb1 = model.encode(query, convert_to_tensor=True)
    emb2 = model.encode(text, convert_to_tensor=True)

    semantic_score = util.cos_sim(emb1, emb2).item()
    semantic_score = (semantic_score + 1) / 2

    query_words = query.lower().split()
    text_lower = text.lower()

    keyword_score = 0

    for word in query_words:
        count = text_lower.count(word)
        keyword_score += min(count, 3)

    if query_words:
        keyword_score = keyword_score / (len(query_words) * 3)
    else:
        keyword_score = 0

    final_score = (0.75 * semantic_score) + (0.25 * keyword_score)

    return round(final_score * 100, 2)


def _calculate_match_scores_batch(query: str, texts: List[str]) -> List[float]:
    if not query or not texts:
        return []

    model = _get_model()
    trimmed_texts = [(text or "")[:500] for text in texts]
    query_embedding = model.encode(query, convert_to_tensor=True)
    text_embeddings = model.encode(trimmed_texts, convert_to_tensor=True)
    semantic_scores = util.cos_sim(query_embedding, text_embeddings)[0].tolist()

    query_words = query.lower().split()
    scores = []

    for semantic_score, text in zip(semantic_scores, trimmed_texts):
        semantic_score = (semantic_score + 1) / 2
        text_lower = text.lower()

        keyword_score = 0
        for word in query_words:
            count = text_lower.count(word)
            keyword_score += min(count, 3)

        if query_words:
            keyword_score = keyword_score / (len(query_words) * 3)
        else:
            keyword_score = 0

        final_score = (0.75 * semantic_score) + (0.25 * keyword_score)
        scores.append(round(final_score * 100, 2))

    return scores


def _extract_profile_title(text: str, role: str) -> str:
    if not text:
        return role

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:5]:
        cleaned = re.sub(r"\s+", " ", re.sub(r"[^A-Za-z0-9,&/#+ .'-]", " ", line)).strip(" ,-")
        if len(cleaned) < 6:
            continue
        if len(cleaned) > 70:
            cleaned = cleaned[:70].rstrip()
        return cleaned.title() if cleaned.upper() == cleaned else cleaned

    return role


def _extract_experience_years(text: str) -> Optional[int]:
    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s+years",
        r"(\d+(?:\.\d+)?)\+?\s+yrs",
        r"(\d+(?:\.\d+)?)\+?\s+year",
        r"(\d+(?:\.\d+)?)\+?\s+yr",
        r"experience\s+of\s+(\d+(?:\.\d+)?)\+?\s+years",
        r"over\s+(\d+(?:\.\d+)?)\s+years",
        r"more\s+than\s+(\d+(?:\.\d+)?)\s+years",
    ]

    lowered = text.lower()
    matches = []
    for pattern in patterns:
        matches.extend(int(float(match)) for match in re.findall(pattern, lowered))

    ranged_years = _infer_experience_from_dates(lowered)
    if ranged_years is not None:
        matches.append(ranged_years)

    return max(matches) if matches else None


def _parse_month_year(month_text: str, year_text: str) -> Optional[datetime]:
    month_key = month_text.strip().lower()[:3] if month_text else "jan"
    month_num = MONTH_MAP.get(month_key) or MONTH_MAP.get(month_text.strip().lower())
    if not month_num:
        month_num = 1
    try:
        return datetime(int(year_text), month_num, 1)
    except Exception:
        return None


def _infer_experience_from_dates(lowered_text: str) -> Optional[int]:
    now = datetime.now()
    spans = []

    month_range_pattern = re.compile(
        r"(?P<start_month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"[\s,\-/]+(?P<start_year>\d{4})\s*(?:to|–|-|until|through)\s*"
        r"(?:(?P<end_month>jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:t|tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
        r"[\s,\-/]+(?P<end_year>\d{4})|(?P<current>present|current|till date))"
    )

    numeric_range_pattern = re.compile(
        r"(?P<start_month>\d{1,2})[/-](?P<start_year>\d{4})\s*(?:to|–|-)\s*"
        r"(?:(?P<end_month>\d{1,2})[/-](?P<end_year>\d{4})|(?P<current>present|current))"
    )

    year_range_pattern = re.compile(
        r"(?P<start_year>19\d{2}|20\d{2})\s*(?:to|–|-)\s*(?P<end_year>19\d{2}|20\d{2}|present|current)"
    )

    for match in month_range_pattern.finditer(lowered_text):
        start = _parse_month_year(match.group("start_month"), match.group("start_year"))
        if not start:
            continue
        if match.group("current"):
            end = now
        else:
            end = _parse_month_year(match.group("end_month"), match.group("end_year"))
        if end and end >= start:
            spans.append((end.year - start.year) + ((end.month - start.month) / 12))

    for match in numeric_range_pattern.finditer(lowered_text):
        try:
            start = datetime(int(match.group("start_year")), int(match.group("start_month")), 1)
        except Exception:
            continue
        if match.group("current"):
            end = now
        else:
            try:
                end = datetime(int(match.group("end_year")), int(match.group("end_month")), 1)
            except Exception:
                continue
        if end >= start:
            spans.append((end.year - start.year) + ((end.month - start.month) / 12))

    for match in year_range_pattern.finditer(lowered_text):
        start_year = int(match.group("start_year"))
        end_year_text = match.group("end_year")
        end_year = now.year if end_year_text in {"present", "current"} else int(end_year_text)
        if end_year >= start_year:
            spans.append(end_year - start_year)


    if not spans:
        return None

    return max(1, int(round(max(spans))))


def _normalize_skill(skill: str) -> str:
    return re.sub(r"\s+", " ", skill.strip().lower())


def _extract_matched_skills(text: str, requested_skills: List[str]) -> List[str]:
    lowered = text.lower()
    matched = []
    for skill in requested_skills:
        normalized = _normalize_skill(skill)
        if normalized and normalized in lowered:
            matched.append(skill)

    if matched:
        return matched

    fallback = []
    for skill in sorted(SOFT_SKILL_KEYWORDS):
        if skill in lowered:
            fallback.append(skill.title())
        if len(fallback) >= 5:
            break
    return fallback


def _build_candidate_insight(profile_title: str, years: Optional[int], matched_skills: List[str], role: str, candidate_id: Optional[str]) -> str:
    insight_parts = [f"Candidate ID {candidate_id} is a strong profile match for the {role} requirement."]
    if profile_title:
        insight_parts.append(f"Resume headline indicates {profile_title}.")

    if years is not None:
        insight_parts.append(f"Estimated experience observed in the resume is around {years}+ years.")
    else:
        insight_parts.append("Experience is not explicitly structured in a standard numeric format, so manual review may help.")

    if matched_skills:
        insight_parts.append(f"Matched skills include {', '.join(matched_skills[:5])}.")
    else:
        insight_parts.append("The resume should be reviewed manually for deeper skill alignment.")

    return " ".join(insight_parts)


def _format_resume_for_display(text: str) -> str:
    if not text:
        return ""

    cleaned = text.replace("\r", "\n")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    for heading in SECTION_HEADINGS:
        pattern = re.compile(rf"(?i)\b{re.escape(heading)}\b")
        cleaned = pattern.sub(lambda m: f"\n\n{m.group(0).upper()}\n", cleaned)

    cleaned = re.sub(r"\s*[•●▪■]\s*", "\n- ", cleaned)
    cleaned = re.sub(r"(?<=[a-z0-9])\s{2,}(?=[A-Z])", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)

    return cleaned.strip()


def _role_terms(role: str) -> List[str]:
    normalized = re.sub(r"\s+", " ", role.lower().strip())
    terms = {word for word in normalized.split() if len(word) > 2}
    for token in list(terms):
        terms.update(ROLE_HINTS.get(token, set()))
    return sorted(terms)


@lru_cache(maxsize=1)
def _candidate_corpus():
    corpus = []
    for candidate_id, resume_text in fetch_all_resumes():
        if _looks_like_binary_or_broken_text(resume_text):
            continue

        full_resume_text = resume_text or ""
        lowered_text = full_resume_text.lower()
        profile_title = _extract_profile_title(full_resume_text, "")
        experience_years = _extract_experience_years(full_resume_text)
        resume_display_text = _format_resume_for_display(full_resume_text)

        corpus.append({
            "candidate_id": str(candidate_id),
            "resume_text": full_resume_text,
            "resume_display_text": resume_display_text,
            "profile_title": profile_title,
            "experience_years": experience_years,
            "lowered_text": lowered_text,
            "lowered_title": profile_title.lower(),
        })

    return tuple(corpus)


def clear_candidate_corpus_cache():
    _candidate_corpus.cache_clear()


# 🔥 IMPORTANT FUNCTION (THIS WAS MISSING)
def run_rag_pipeline(query):

    results = retrieve_candidates(query)

    docs = results.get("documents", [[]])[0]
    ids = results.get("ids", [[]])[0]

    valid_pairs = []
    for i in range(len(docs)):
        resume_text = docs[i]
        candidate_id = ids[i] if i < len(ids) else None
        if _looks_like_binary_or_broken_text(resume_text):
            continue
        valid_pairs.append((candidate_id, resume_text))

    batched_scores = _calculate_match_scores_batch(query, [resume_text for _, resume_text in valid_pairs])
    output = []

    for (candidate_id, resume_text), score in zip(valid_pairs, batched_scores):
        output.append({
            "candidate_id": candidate_id,
            "resume_preview": resume_text[:200],
            "full_resume_text": resume_text,
            "match_score": f"{score}%"
        })

    output = sorted(
        output,
        key=lambda x: float(x["match_score"].replace("%", "")),
        reverse=True
    )

    return {
        "candidates": output
    }


def run_llm_rag_pipeline(query):
    result = run_rag_pipeline(query)
    candidates = result.get("candidates", [])

    return {
        "candidates": candidates,
        "llm_enabled": llm_is_configured(),
        "llm_insights": generate_llm_insights(query, candidates),
    }


def run_candidate_search(role: str, experience_value: str, additional_skills: List[str]):
    query_parts = [role.strip()]
    if additional_skills:
        query_parts.extend(additional_skills)
    query = " ".join(part for part in query_parts if part).strip()

    candidates = []

    min_years = None
    if experience_value and experience_value != "Any":
        min_years = 6 if experience_value == "6+ years" else int(experience_value.split()[0])

    role_words = _role_terms(role)
    requested_skill_count = len(additional_skills)
    scored_candidates = []

    for candidate in _candidate_corpus():
        years = candidate["experience_years"]

        if min_years is not None and years is not None and years < min_years:
            continue

        full_resume_text = candidate["resume_text"]
        profile_title = candidate["profile_title"] or role
        matched_skills = _extract_matched_skills(full_resume_text, additional_skills)
        candidate_insight = _build_candidate_insight(profile_title, years, matched_skills, role, candidate["candidate_id"])

        lowered_text = candidate["lowered_text"]
        role_match_ratio = (
            sum(1 for word in role_words if word in lowered_text) / len(role_words)
            if role_words else 0.0
        )
        title_match_ratio = (
            sum(1 for word in role_words if word in candidate["lowered_title"]) / len(role_words)
            if role_words else 0.0
        )
        skill_match_ratio = (
            len(matched_skills) / requested_skill_count
            if requested_skill_count else 0.0
        )
        if role_words:
            if title_match_ratio == 0 and role_match_ratio < 0.15:
                continue

        if min_years is not None:
            if years is None:
                experience_match_ratio = 0.35
            else:
                experience_match_ratio = min(years / max(min_years, 1), 1.0)
        else:
            experience_match_ratio = 0.65 if years is None else min(years / 10.0, 1.0)

        score_value = (
            28.0
            + (24.0 * role_match_ratio)
            + (22.0 * title_match_ratio)
            + (16.0 * skill_match_ratio)
            + (10.0 * experience_match_ratio)
        )
        score_value = min(96.0, round(score_value, 2))

        scored_candidates.append((score_value, {
            "candidate_id": candidate["candidate_id"],
            "candidate_title": profile_title,
            "candidate_insights": candidate_insight,
            "candidate_score": f"{score_value}%",
            "experience_years": years,
            "experience_display": f"{years}+ years" if years is not None else "Resume needs manual experience review",
            "matched_skills": matched_skills,
            "resume_text": full_resume_text,
            "resume_display_text": candidate["resume_display_text"],
        }))

    scored_candidates.sort(key=lambda item: item[0], reverse=True)
    candidates = [candidate for _, candidate in scored_candidates[:10]]

    return {
        "query": query,
        "filters": {
            "role": role,
            "experience": experience_value,
            "additional_skills": additional_skills,
        },
        "candidates": candidates[:10],
    }
