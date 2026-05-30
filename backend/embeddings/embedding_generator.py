from sentence_transformers import SentenceTransformer

# 🔥 Load model only once (VERY IMPORTANT for performance)
_MODEL = None


def _get_model():
    global _MODEL
    if _MODEL is None:
        try:
            _MODEL = SentenceTransformer("sentence-transformers/all-mpnet-base-v2", local_files_only=True)
        except Exception:
            _MODEL = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
    return _MODEL


def generate_embeddings(texts):
    """
    Generate embeddings for a list of resume texts
    """

    if not texts:
        return []

    # 🔥 Generate embeddings in batch (fast)
    model = _get_model()
    embeddings = model.encode(
        texts,
        batch_size=32,          # improves speed
        show_progress_bar=True  # optional (can remove if not needed)
    )

    # Convert to list for ChromaDB
    return embeddings.tolist()
