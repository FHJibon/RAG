from collections import Counter
from app.model.pinecone_db import init_pinecone, query
from app.model.embeddings import embed_texts
from app.config import TOP_K


def _compute_lexical_score(query_text: str, doc_text: str) -> float:
    if not query_text or not doc_text:
        return 0.0
    q_tokens = [t.lower() for t in query_text.split() if t.strip()]
    d_tokens = [t.lower() for t in doc_text.split() if t.strip()]
    if not q_tokens or not d_tokens:
        return 0.0
    q_counts = Counter(q_tokens)
    d_counts = Counter(d_tokens)
    overlap = 0
    for term, qc in q_counts.items():
        if term in d_counts:
            overlap += min(qc, d_counts[term])
    return overlap / max(1, len(q_tokens))


def retrieve_top_chunks(query_text: str, k: int = None):
    idx = init_pinecone()
    k = k or TOP_K
    emb = embed_texts([query_text])[0]
    matches = query(idx, emb, top_k=max(k * 2, k + 5), include_values=False)

    hybrid_results = []
    for m in matches:
        md = m.get("metadata", {}) or {}
        doc_text = md.get("text") or ""
        vec_score = float(m.get("score", 0.0))
        lex_score = _compute_lexical_score(query_text, doc_text)
        final_score = 0.7 * vec_score + 0.3 * lex_score
        hybrid_results.append({
            "id": m.get("id"),
            "score": final_score,
            "metadata": md,
        })

    hybrid_results.sort(key=lambda x: x["score"], reverse=True)
    return hybrid_results[:k]