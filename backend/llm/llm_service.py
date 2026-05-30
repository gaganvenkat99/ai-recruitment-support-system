import json
import os
from urllib import error, request

from backend.config import LLM_PROVIDER, OLLAMA_BASE_URL, OLLAMA_MODEL, OPENAI_MODEL


def _build_candidate_context(candidates):
    lines = []

    for index, candidate in enumerate(candidates[:5], start=1):
        lines.append(
            f"Candidate {index}: "
            f"ID={candidate.get('candidate_id')}, "
            f"Score={candidate.get('match_score')}, "
            f"Resume Preview={candidate.get('resume_preview', '')}"
        )

    return "\n".join(lines)


def _make_prompt(query, candidates):
    candidate_context = _build_candidate_context(candidates)

    return (
        "You are an AI recruiter assistant.\n"
        "Analyze the top candidates for the job query below.\n"
        "Return short, practical hiring insights in plain English.\n"
        "Include:\n"
        "1. Best overall candidate\n"
        "2. Why they match\n"
        "3. Top missing skills or risks\n"
        "4. Short recommendation\n\n"
        f"Job Query: {query}\n\n"
        f"Candidates:\n{candidate_context}"
    )


def _post_json(url, payload, headers=None):
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )

    with request.urlopen(req, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))


def _call_openai(prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", OPENAI_MODEL)

    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    response = _post_json(
        "https://api.openai.com/v1/chat/completions",
        {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a concise recruiter assistant.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            "temperature": 0.2,
        },
        headers={"Authorization": f"Bearer {api_key}"},
    )

    return response["choices"][0]["message"]["content"].strip()


def _call_ollama(prompt):
    base_url = os.getenv("OLLAMA_BASE_URL", OLLAMA_BASE_URL)
    model = os.getenv("OLLAMA_MODEL", OLLAMA_MODEL)

    response = _post_json(
        f"{base_url}/api/generate",
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
        },
    )

    return response.get("response", "").strip()


def llm_is_configured():
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()

    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))

    return True


def generate_llm_insights(query, candidates):
    if not candidates:
        return "No candidates were found for this query."

    prompt = _make_prompt(query, candidates)
    provider = os.getenv("LLM_PROVIDER", LLM_PROVIDER).lower()

    try:
        if provider == "openai":
            return _call_openai(prompt)

        return _call_ollama(prompt)
    except error.URLError as exc:
        return (
            "LLM connection failed. "
            f"Please check your {provider} setup. Details: {exc}"
        )
    except Exception as exc:
        return f"LLM generation failed: {exc}"
