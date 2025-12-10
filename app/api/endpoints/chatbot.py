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
        lines.append(f"{i+1}. id:{m.get('id')} page:{md.get('page')} score:{m.get('score')}")
    return "\n".join(lines)

def extract_json(text):
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
        temperature=0.3,
    )

    raw = resp.choices[0].message.content.strip()
    try:
        out = json.loads(raw)
    except Exception:
        out = extract_json(raw)

    answer = out.get("answer", "") if isinstance(out, dict) else "(assistant did not return valid JSON)"
    citations_out = []
    if not out or not isinstance(out, dict):
        # fallback: return top-1 retrieved chunk as citation
        m = matches[0] if matches else {}
        md = m.get("metadata", {}) or {}
        citations_out.append(Citation(
            page=md.get("page"),
            score=m.get("score")
        ))
        return ChatResponse(answer=answer, citations=citations_out)

    llm_cits = out.get("citations", [])
    if isinstance(llm_cits, list) and llm_cits:
        c = llm_cits[0]
        citations_out.append(Citation(
            page=c.get("page"),
            score=c.get("score")
        ))
    else:
        m = matches[0] if matches else {}
        md = m.get("metadata", {}) or {}
        citations_out.append(Citation(
            page=md.get("page"),
            score=m.get("score")
        ))

    return ChatResponse(answer=answer, citations=citations_out)