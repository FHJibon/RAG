def clean_pdf_text(text: str) -> str:
    if not text:
        return ""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        l = line.strip()
        if re.fullmatch(r'\d{1,4}', l):
            continue
        if len(re.sub(r'[^a-zA-Z0-9]', '', l)) < 5:
            continue
        cleaned.append(l)
    return '\n'.join(cleaned)
import re
from typing import List

def split_paragraphs(text: str) -> List[str]:
    if not text:
        return []
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paras = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    if not paras:
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        paras = []
        buffer = []
        for line in lines:
            buffer.append(line)
            if len(" ".join(buffer)) > 200:
                paras.append(" ".join(buffer))
                buffer = []
        if buffer:
            paras.append(" ".join(buffer))
    return paras