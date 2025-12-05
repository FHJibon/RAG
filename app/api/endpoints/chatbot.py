# api/endpoints/chatbot.py
from fastapi import APIRouter, HTTPException
from typing import List
from app.schemas.chat_schema import ChatRequest, ChatResponse, Citation
from app.services.retriever import retrieve_top_chunks
from app.services.llm import parse_tax_fields_from_text
from app.services.tax_engine import compute_tax
import openai
from app.config import OPENAI_CHAT_MODEL, OPENAI_API_KEY
from prompts.chat_prompt import CHAT_PROMPT_TEMPLATE
from app.prompts.chat_prompt import CHAT_PROMPT_TEMPLATE
import json

openai.api_key = OPENAI_API_KEY
router = APIRouter()

def build_chunks_for_prompt(matches: List[dict]) -> str:
    lines = []
    for i, m in enumerate(matches):
        md = m.get("metadata", {}) or {}
        lines.append(f"{i+1}. id:{m.get('id')} sec:{md.get('section_id')} page:{md.get('page')} score:{m.get('score')}")
    return "\n".join(lines)

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="question required")

    matches = retrieve_top_chunks(req.question)

    chunks_text = build_chunks_for_prompt(matches)
    prompt = CHAT_PROMPT_TEMPLATE.format(question=req.question, chunks_text=chunks_text)

    resp = openai.ChatCompletion.create(
        model=OPENAI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": "Reply with strict JSON only."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=700,
        temperature=0.0,
    )

    raw = resp.choices[0].message.content.strip()
    try:
        out = json.loads(raw)
    except Exception:
        citations = []
        for m in matches:
            md = m.get("metadata", {}) or {}
            citations.append(Citation(
                chunk_id=m.get("id"),
                section_id=md.get("section_id"),
                page=md.get("page"),
                score=m.get("score")
            ))
        return ChatResponse(
            answer="(assistant did not return valid JSON)",
            citations=citations,
            tax_mode=False
        )

    tax_mode = bool(out.get("tax_mode", False))
    calc_values = None
    calc_expl = out.get("calculation_explanation")

    if tax_mode:
        source_text = req.user_text or req.question
        parsed = parse_tax_fields_from_text(source_text)
        calc_values = compute_tax(parsed)
    citations_out = []
    llm_cits = out.get("citations", [])
    if isinstance(llm_cits, list) and llm_cits:
        for c in llm_cits:
            citations_out.append(Citation(
                chunk_id=c.get("chunk_id"),
                section_id=c.get("section_id"),
                page=c.get("page"),
                score=c.get("score")
            ))
    else:
        for m in matches:
            md = m.get("metadata", {}) or {}
            citations_out.append(Citation(
                chunk_id=m.get("id"),
                section_id=md.get("section_id"),
                page=md.get("page"),
                score=m.get("score")
            ))

    return ChatResponse(
        answer=out.get("answer", ""),
        citations=citations_out,
        tax_mode=tax_mode,
        calculation_explanation=calc_expl,
        calculation_values=calc_values
    )