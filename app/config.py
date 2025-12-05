import os
from dotenv import load_dotenv

load_dotenv()

DATA_PDF_PATH = "app/data/DATA.pdf"

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBED_MODEL = "text-embedding-3-small"
OPENAI_CHAT_MODEL = "gpt-4o"

CHUNK_MIN_LEN = 30
AGENT_CONFIDENCE_THRESHOLD = 0.2

TOP_K = 5

TAX_SLABS = [
    {"limit": 300000, "rate": 0.0},   
    {"limit": 700000, "rate": 0.05},  
    {"limit": 1500000, "rate": 0.10},
    {"limit": None, "rate": 0.15},
]