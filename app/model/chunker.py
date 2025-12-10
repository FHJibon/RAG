from pathlib import Path
import uuid
from typing import List, Dict, Any
from pypdf import PdfReader
from app.utils.clean import split_paragraphs
from app.config import CHUNK_MIN_LEN

def extract_paragraphs_from_pdf(pdf_path: str) -> List[Dict[str, Any]]:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"{pdf_path} not found")
    reader = PdfReader(str(path))
    pages = []
    for idx, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        paras = split_paragraphs(text)
        pages.append((idx, paras))
    out = []
    for page_num, paras in pages:
        for pidx, p in enumerate(paras):
            if not p or len(p) < CHUNK_MIN_LEN:
                continue
            out.append({"page": page_num, "paragraph_index": pidx, "text": p})
    return out

def _approx_token_len(text: str) -> int:
    return max(1, len(text) // 4)


def _merge_paragraphs_hierarchical(paras: List[Dict[str, Any]],paragraph_overlap: int = 0,) -> List[Dict[str, Any]]:
    if not paras:
        return []

    chunks: List[Dict[str, Any]] = []
    n = len(paras)

    for i, para in enumerate(paras):
        texts = [para["text"]]

        for j in range(1, paragraph_overlap + 1):
            prev_idx = i - j
            if prev_idx < 0:
                break
            texts.insert(0, paras[prev_idx]["text"])

        chunk_text = "\n\n".join(texts)
        chunk = {
            "id": str(uuid.uuid4()),
            "text": chunk_text,
            "page": para["page"],
        }
        chunks.append(chunk)

    return chunks


def build_pdf_chunks(pdf_path: str) -> List[Dict[str, Any]]:
    raw_paras = extract_paragraphs_from_pdf(pdf_path)
    chunks = _merge_paragraphs_hierarchical(raw_paras, paragraph_overlap=0)
    return chunks