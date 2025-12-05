from typing import List
import openai
from config import OPENAI_EMBED_MODEL, OPENAI_API_KEY

openai.api_key = OPENAI_API_KEY

def embed_texts(texts: List[str], model: str = OPENAI_EMBED_MODEL) -> List[List[float]]:
    if not texts:
        return []
    resp = openai.Embedding.create(model=model, input=texts)
    return [d["embedding"] for d in resp["data"]]