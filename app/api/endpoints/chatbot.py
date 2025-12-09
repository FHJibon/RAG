from fastapi import APIRouter, HTTPException
from app.schemas.chat_schema import ChatRequest, ChatResponse, Citation
from app.services.retriever import retrieve_top_chunks
import openai
from app.config import OPENAI_CHAT_MODEL, OPENAI_API_KEY
from app.prompts.chat_prompt import CHAT_PROMPT_TEMPLATE
import json

client = openai.OpenAI(api_key=OPENAI_API_KEY)
router = APIRouter()

def build_chunks_for_prompt(matches):
    lines = []
    for i, m in enumerate(matches):
        md = m.get("metadata", {}) or {}
        lines.append(f"{i+1}. id:{m.get('id')} sec:{md.get('section_id')} page:{md.get('page')} score:{m.get('score')}")
    return "\n".join(lines)

def extract_json(text):
    """Extract the first valid JSON object from a string."""
    import re
    import json
    match = re.search(r'{.*}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass
    return None

@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="question required")

    matches = retrieve_top_chunks(req.question)
    chunks_text = build_chunks_for_prompt(matches)
    prompt = CHAT_PROMPT_TEMPLATE.format(question=req.question, chunks_text=chunks_text)

    resp = client.chat.completions.create(
        model=OPENAI_CHAT_MODEL,
        messages=[
            {"role": "system", "content": "Reply with a single valid JSON object only. Do not include any text outside the JSON object."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=700,
        temperature=0.0,
    )

    raw = resp.choices[0].message.content.strip()
    out = None
    try:
        out = json.loads(raw)
    except Exception:
        out = extract_json(raw)

    citations_out = []
    if not out or not isinstance(out, dict):
        # Always return a valid response
        for m in matches:
            md = m.get("metadata", {}) or {}
            citations_out.append(Citation(
                chunk_id=m.get("id"),
                section_id=md.get("section_id"),
                page=md.get("page"),
                score=m.get("score")
            ))
        return ChatResponse(
            answer="(assistant did not return valid JSON)",
            citations=citations_out,
        )

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
        answer=out.get("answer", "") if isinstance(out, dict) else "(assistant did not return valid JSON)",
        citations=citations_out,
    )