from pathlib import Path
import uuid
from typing import List, Dict, Any
from pypdf import PdfReader
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

def _approx_token_len(text: str) -> int:
    return max(1, len(text) // 4)


def _merge_paragraphs_hierarchical(paras: List[Dict[str, Any]],
                                   min_tokens: int = 200,
                                   max_tokens: int = 1500,
                                   overlap_ratio: float = 0.15) -> List[Dict[str, Any]]:
    if not paras:
        return []

    chunks: List[Dict[str, Any]] = []
    i = 0
    n = len(paras)

    target_tokens = (min_tokens + max_tokens) // 2
    overlap_tokens = int(target_tokens * overlap_ratio)

    while i < n:
        current_texts = []
        current_metas = []
        current_tokens = 0
        start_i = i

        while i < n and current_tokens < max_tokens:
            para = paras[i]
            t = para["text"]
            tokens = _approx_token_len(t)
            if current_tokens >= min_tokens and current_tokens + tokens > max_tokens:
                break
            current_texts.append(t)
            current_metas.append(para)
            current_tokens += tokens
            i += 1

        if not current_texts:
            para = paras[i]
            current_texts.append(para["text"])
            current_metas.append(para)
            i += 1

        merged_text = "\n\n".join(current_texts)
        first = current_metas[0]
        chunk = {
            "id": str(uuid.uuid4()),
            "text": merged_text,
            "section_id": "auto", 
            "page": first["page"],
            "paragraph_index": first["paragraph_index"],
            "confidence": 1.0,
        }
        chunks.append(chunk)

        if i >= n:
            break
        back_tokens = 0
        j = i - 1
        while j > start_i and back_tokens < overlap_tokens:
            back_tokens += _approx_token_len(paras[j]["text"])
            j -= 1
        i = max(j + 1, start_i + 1)

    return chunks


def build_pdf_chunks(pdf_path: str) -> List[Dict[str, Any]]:
    raw_paras = extract_paragraphs_from_pdf(pdf_path)
    print(f"[Chunker] Building chunks from {len(raw_paras)} paragraphs...")
    chunks = _merge_paragraphs_hierarchical(raw_paras)
    print(f"[Chunker] Finished chunking. Chunks to store: {len(chunks)}")
    return chunks