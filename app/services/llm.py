import json
import time
from openai import OpenAI, RateLimitError
from app.config import OPENAI_API_KEY, OPENAI_CHAT_MODEL, OPENAI_EMBED_MODEL
from app.prompts.chunk_prompt import CHUNK_PROMPT_TEMPLATE

client = OpenAI(api_key=OPENAI_API_KEY)


def _strip_markdown_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = [l for l in text.splitlines() if l.strip()]
        if not lines:
            return ""
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        if lines and lines[0].lower().startswith("json"):
            lines[0] = lines[0][4:].lstrip()
        return "\n".join(lines).strip()
    return text


def agent_decide_chunk(paragraph: str, chat_model: str | None = None) -> dict:
    model = chat_model or OPENAI_CHAT_MODEL
    prompt = CHUNK_PROMPT_TEMPLATE.format(paragraph=paragraph.replace('"', "'"))
    print("[LLM] agent_decide_chunk: calling model=", model)

    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You must respond only in JSON."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.0,
            )
            break
        except RateLimitError as e:
            wait = 1 + attempt  # 1s, 2s, 3s
            print(f"[LLM] Rate limit hit (attempt {attempt+1}), sleeping {wait}s: {e}")
            time.sleep(wait)
    else:
        return {"store": False, "section_id": "unknown", "confidence": 0.0}

    raw = resp.choices[0].message.content.strip()
    print("[LLM] Raw response:", raw[:400], "...")
    text = _strip_markdown_fence(raw)
    try:
        parsed = json.loads(text)
        print("[LLM] Parsed decision:", parsed)
        if isinstance(parsed, list):
            for item in parsed:
                if isinstance(item, dict) and item.get("store"):
                    return item
            if parsed and isinstance(parsed[0], dict):
                return parsed[0]
            return {"store": False, "section_id": "unknown", "confidence": 0.0}
        if isinstance(parsed, dict):
            return parsed
        return {"store": False, "section_id": "unknown", "confidence": 0.0}
    except Exception as e:
        print("[LLM] JSON parse error after fence strip:", e)
        return {"store": False, "section_id": "unknown", "confidence": 0.0}


def embed_text(texts, embed_model: str | None = None):
    model = embed_model or OPENAI_EMBED_MODEL
    resp = client.embeddings.create(model=model, input=texts)
    return [d.embedding for d in resp.data]


def parse_tax_fields_from_text(user_text: str, chat_model: str | None = None) -> dict:
    model = chat_model or OPENAI_CHAT_MODEL
    prompt = f"""
Extract the following fields from the user's text. Return ONLY valid JSON.
Fields:
- full_name (string or null)
- tin (string or null)
- nid (string or null)
- fiscal_year (string or null)
- gross_salary (number or null)
- allowances (number or null)
- exemptions (number or null)
- tax_already_paid (number or null)

If a field isn't present, return null.
User text:
\"\"\"{user_text}\"\"\"
"""
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You must reply with strict JSON."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=800,
        temperature=0.0,
    )
    text = resp.choices[0].message.content.strip()
    try:
        parsed = json.loads(text)
    except Exception:
        parsed = {
            "full_name": None,
            "tin": None,
            "nid": None,
            "fiscal_year": None,
            "gross_salary": None,
            "allowances": None,
            "exemptions": None,
            "tax_already_paid": None,
        }
    for k in ("gross_salary", "allowances", "exemptions", "tax_already_paid"):
        v = parsed.get(k)
        try:
            parsed[k] = None if v is None else float(v)
        except Exception:
            parsed[k] = None
    return parsed