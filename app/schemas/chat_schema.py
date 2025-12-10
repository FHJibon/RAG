from pydantic import BaseModel
from typing import Optional, List

class Citation(BaseModel):
    page: int
    score: Optional[float] = None

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]