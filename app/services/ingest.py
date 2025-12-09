from app.model.chunker import build_pdf_chunks
from app.model.pinecone_db import init_pinecone, upsert_batch
from app.model.embeddings import embed_texts
from app.config import DATA_PDF_PATH, PINECONE_INDEX
import json
import os

def run_ingest(pdf_path: str = DATA_PDF_PATH, index_name: str = None):
    print("Starting ingestion (hierarchical chunking)...")
    chunks = build_pdf_chunks(pdf_path)
    print(f"Chunks to store: {len(chunks)}")
    if not chunks:
        print("No chunks found. Exiting.")
        return

    index = init_pinecone(index_name)
    texts = [c["text"] for c in chunks]
    embeddings = embed_texts(texts)
    vectors = []
    for c, emb in zip(chunks, embeddings):
        metadata = {
            "section_id": c["section_id"],
            "page": c["page"],
            "paragraph_index": c["paragraph_index"],
            "confidence": c["confidence"],
            "source": "DATA.pdf",
            "text": c["text"]
        }
        vectors.append({"id": c["id"], "values": emb, "metadata": metadata})

    print("Upserting to Pinecone...")
    upsert_batch(index, vectors)
    print("Ingest complete. Indexed chunks:", len(vectors))

if __name__ == "__main__":
    run_ingest()