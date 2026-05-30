import chromadb

# ✅ Persistent client (VERY IMPORTANT)
client = chromadb.PersistentClient(path="vector_db")

# ✅ Collection
collection = client.get_or_create_collection(name="resumes")


def reset_collection():
    global collection

    try:
        client.delete_collection(name="resumes")
    except Exception:
        pass

    collection = client.get_or_create_collection(name="resumes")
    return collection

def store_embedding(resume_id, embedding, text):

    collection.add(
        ids=[str(resume_id)],
        embeddings=[embedding],
        documents=[text]
    )
