from backend.database.models import fetch_all_resumes

# 🔥 Load model once
model = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")

def retrieve_candidates(query):

    # Convert query → embedding
    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=10   # 🔥 Top 10 candidates
    )

    return results
