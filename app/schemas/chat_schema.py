from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class Citation(BaseModel):
    chunk_id: Optional[str] = Field(None)
    section_id: Optional[str] = Field(None)
    page: Optional[int] = Field(None)
    score: Optional[float] = Field(None)

class ChatRequest(BaseModel):
    question: str = Field(..., description="User question")
    user_text: Optional[str] = Field(None, description="Optional structured text")

class ChatResponse(BaseModel):
    answer: str
    citations: List[Citation]
    tax_mode: bool = False
    calculation_explanation: Optional[str] = None
    calculation_values: Optional[Dict[str, Any]] = None