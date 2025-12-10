import time
from typing import List, Dict, Any
from pinecone import Pinecone, ServerlessSpec 

try:
    from app.config import PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX
except ModuleNotFoundError:
    import os, sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
    from app.config import PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX

def init_pinecone(index_name=None):
    target_index = index_name or PINECONE_INDEX

    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY is missing")
    if not target_index:
        raise ValueError("Index name is missing")

    pc = Pinecone(api_key=PINECONE_API_KEY)

    existing_indexes = [i.name for i in pc.list_indexes()]

    if target_index not in existing_indexes:
        pc.create_index(
            name=target_index,
            dimension=3072,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region=PINECONE_ENV
            )
        )
        while not pc.describe_index(target_index).status['ready']:
            time.sleep(1)

    return pc.Index(target_index)

def upsert_batch(index, vectors: List[Dict[str, Any]]):
    if not vectors:
        return
    batch_size = 50
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i+batch_size]
        index.upsert(vectors=[
            {
                "id": v["id"], 
                "values": v["values"], 
                "metadata": v.get("metadata", {})
            } for v in batch
        ])

def query(index, vector, top_k=6, include_values=False):
    res = index.query(
        vector=vector, 
        top_k=top_k, 
        include_values=include_values, 
        include_metadata=True
    )
    return res.get("matches", [])
