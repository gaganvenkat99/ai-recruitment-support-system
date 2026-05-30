from fastapi import UploadFile
from typing import List

from backend.resume_processing.resume_parser_v2 import parse_resume
from backend.database.models import insert_resume
from backend.embeddings.embedding_generator import generate_embeddings
from backend.embeddings.vector_store import collection


async def upload_resume_bulk(files: list[UploadFile]):   # ✅ IMPORTANT

    uploaded = []
    failed = []

    for file in files:
        try:
            text = await parse_resume(file)

            resume_id = insert_resume(text, "uploaded")

            embedding = generate_embeddings([text])[0]

            collection.add(
                ids=[str(resume_id)],
                embeddings=[embedding],
                documents=[text]
            )

            uploaded.append(file.filename)
        except Exception as exc:
            failed.append({
                "file": file.filename,
                "error": str(exc),
            })

    return {
        "uploaded": uploaded,
        "failed": failed,
        "total": len(files),
    }
