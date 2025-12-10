from typing import List
import openai
from app.config import OPENAI_EMBED_MODEL, OPENAI_API_KEY

client = openai.OpenAI(api_key=OPENAI_API_KEY)

def embed_texts(texts: List[str], model: str = OPENAI_EMBED_MODEL) -> List[List[float]]:
    if not texts:
        return []

    str_texts = ["" if t is None else str(t) for t in texts]
    embeddings: List[List[float]] = []
    batch_size = 256
    for i in range(0, len(str_texts), batch_size):
        batch = str_texts[i:i + batch_size]
        resp = client.embeddings.create(model=model, input=batch)
        embeddings.extend([d.embedding for d in resp.data])
    return embeddings