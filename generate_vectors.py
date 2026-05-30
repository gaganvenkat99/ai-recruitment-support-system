from backend.embeddings.embedding_generator import generate_embeddings
from backend.embeddings.vector_store import store_embedding

print("Generating embeddings...")

data = generate_embeddings()

count = 0

for resume_id, embedding, text in data:

    store_embedding(resume_id, embedding, text)

    count += 1

    if count % 100 == 0:
        print(f"{count} resumes processed...")

print(f"Vector database created successfully with {count} resumes")