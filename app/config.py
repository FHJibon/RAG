import os
from dotenv import load_dotenv

load_dotenv()

DATA_PDF_PATH = "app/data/DATA.pdf" 

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = "us-east-1"
PINECONE_INDEX = "tax-law"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_EMBED_MODEL = "text-embedding-3-small"
OPENAI_CHAT_MODEL = "gpt-4o"

CHUNK_MIN_LEN = 30

TOP_K = 5