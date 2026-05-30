import sqlite3

from backend.embeddings.embedding_generator import generate_embeddings
from backend.embeddings.vector_store import collection, reset_collection


def looks_like_broken_text(text: str) -> bool:
    if not text:
        return True

    sample = text[:200].lower()
    return any(
        marker in sample
        for marker in ("%pdf-", "endobj", "/type/catalog", "xref", "stream")
    )


def fetch_resumes():
    conn = sqlite3.connect("recruitment.db")
    cur = conn.cursor()
    cur.execute("SELECT id, resume_text FROM resumes ORDER BY id")
    rows = cur.fetchall()
    conn.close()
    return rows


def main():
    rows = fetch_resumes()
    valid_rows = [(resume_id, text) for resume_id, text in rows if not looks_like_broken_text(text)]

    reset_collection()

    batch_size = 64
    inserted = 0

    for start in range(0, len(valid_rows), batch_size):
        batch = valid_rows[start:start + batch_size]
        ids = [str(resume_id) for resume_id, _ in batch]
        texts = [text for _, text in batch]
        embeddings = generate_embeddings(texts)

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
        )

        inserted += len(batch)
        print(f"Inserted {inserted}/{len(valid_rows)} resumes")

    print(f"Vector store rebuilt successfully with {inserted} resumes")
    print(f"Skipped {len(rows) - len(valid_rows)} broken resumes")


if __name__ == "__main__":
    main()
