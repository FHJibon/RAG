from app.model.pinecone_db import init_pinecone, query
from app.services.llm import embed_text
from app.config import TOP_K

def retrieve_top_chunks(query_text: str, k: int = None):
    idx = init_pinecone()
    k = k or TOP_K
    emb = embed_text([query_text])[0]
    matches = query(idx, emb, top_k=k, include_values=False)
    results = []
    for m in matches:
        results.append({
            "id": m["id"],
            "score": m["score"],
            "metadata": m.get("metadata", {})
        })
    return results