from functools import lru_cache

from backend.database.db_connection import get_connection


def clear_resume_cache():
    _fetch_all_resumes_cached.cache_clear()
    try:
        from backend.rag.rag_engine import clear_candidate_corpus_cache
        clear_candidate_corpus_cache()
    except Exception:
        pass

def insert_resume(text, source):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO resumes (resume_text, source) VALUES (?,?)",
        (text, source)
    )

    resume_id = cursor.lastrowid
    conn.commit()
    conn.close()
    clear_resume_cache()

    return resume_id


def fetch_all_resumes():
    return list(_fetch_all_resumes_cached())


@lru_cache(maxsize=1)
def _fetch_all_resumes_cached():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id,resume_text FROM resumes")

    rows = cursor.fetchall()

    conn.close()

    return tuple(rows)


def fetch_resume_by_id(resume_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id, resume_text, source FROM resumes WHERE id = ?",
        (resume_id,)
    )

    row = cursor.fetchone()

    conn.close()

    return row
