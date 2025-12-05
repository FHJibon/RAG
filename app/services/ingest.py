from app.model.chunker import chunk_pdf_agentic
from app.model.pinecone_db import init_pinecone, upsert_batch
from app.services.llm import embed_text
from app.config import DATA_PDF_PATH, PINECONE_INDEX
import json
import os

def run_ingest(pdf_path: str = DATA_PDF_PATH, index_name: str = None):
    print("Starting ingestion (agentic chunking)...")
    chunks = chunk_pdf_agentic(pdf_path)
    print(f"Agent selected {len(chunks)} chunks to store.")
    if not chunks:
        print("No chunks found. Exiting.")
        return

    index = init_pinecone(index_name)
    texts = [c["text"] for c in chunks]
    embeddings = embed_text(texts)
    vectors = []
    for c, emb in zip(chunks, embeddings):
        metadata = {
            "section_id": c["section_id"],
            "page": c["page"],
            "paragraph_index": c["paragraph_index"],
            "confidence": c["confidence"],
            "source": "DATA.pdf"
        }
        vectors.append({"id": c["id"], "values": emb, "metadata": metadata})

    print("Upserting to Pinecone...")
    upsert_batch(index, vectors)
    print("Ingest complete. Indexed chunks:", len(vectors))

if __name__ == "__main__":
    run_ingest()