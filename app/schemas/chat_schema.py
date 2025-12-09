from pydantic import BaseModel, Field
from typing import Optional, List

class Citation(BaseModel):
    section_id: Optional[str] = None
    page: Optional[int] = None
    score: Optional[float] = None

class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]