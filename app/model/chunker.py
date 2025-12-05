from pathlib import Path
import uuid
import time
from typing import List, Dict, Any
from pypdf import PdfReader
from app.services.llm import agent_decide_chunk
from app.utils.clean import split_paragraphs
from app.config import CHUNK_MIN_LEN

def extract_paragraphs_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    print(f"[Chunker] Parsing PDF: {pdf_path}")
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"{pdf_path} not found")
    reader = PdfReader(str(path))
    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        paras = split_paragraphs(text)
        print(f"[Chunker] Page {idx}: {len(paras)} paragraphs")
        pages.append((idx, paras))
    out = []
    for page_num, paras in pages:
        for pidx, p in enumerate(paras):
            if not p or len(p) < CHUNK_MIN_LEN:
                continue
            out.append({"page": page_num, "paragraph_index": pidx, "text": p})
    print(f"[Chunker] Total paragraphs to process: {len(out)}")
    return out

def chunk_pdf_agentic(pdf_path: str, chat_model: str = None) -> List[Dict[str, Any]]:
    raw_paras = extract_paragraphs_from_pdf(pdf_path)
    chunks = []
    print(f"[Chunker] Starting LLM chunking for {len(raw_paras)} paragraphs...")
    for i, item in enumerate(raw_paras):
        print(f"[Chunker] LLM chunking paragraph {i+1}/{len(raw_paras)} (page {item['page']}, para {item['paragraph_index']})")
        decision = agent_decide_chunk(item["text"], chat_model=chat_model)
        time.sleep(0.05)
        if decision.get("store"):
            chunk = {
                "id": str(uuid.uuid4()),
                "text": item["text"],
                "section_id": decision.get("section_id", "unknown"),
                "page": item["page"],
                "paragraph_index": item["paragraph_index"],
                "confidence": float(decision.get("confidence", 0.0))
            }
            chunks.append(chunk)
    print(f"[Chunker] Finished chunking. Chunks to store: {len(chunks)}")
    return chunks