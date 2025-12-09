import re
from typing import List

def split_paragraphs(text: str) -> List[str]:
    lines = text.splitlines()
    cleaned_paragraphs = []
    buffer = "" 
    section_pattern = re.compile(r'^(\d+\.|[\(\[]\w+[\)\]]|\*+)')
    garbage_pattern = re.compile(r'[†‡¶¨³µÅÖ]')
    header_pattern = re.compile(
        r'(Government of the People|National Board of Revenue|NOTIFICATION|S\.R\.O No|Dated:|Authentic English Text)',
        re.IGNORECASE
    )

    for line in lines:
        line = line.strip()
        if not line: continue
        if re.fullmatch(r'\d{1,6}', line): continue
        if garbage_pattern.search(line): continue
        if header_pattern.search(line): continue
        if re.match(r'^\d+\s+The words.*substituted', line): continue
        if section_pattern.match(line):
            if buffer:
                cleaned_paragraphs.append(buffer)
            buffer = line
        else:
            if buffer:
                if buffer.endswith('-'):
                    buffer = buffer[:-1] + line 
                else:
                    buffer += " " + line
            else:
                buffer = line
   
    if buffer:
        cleaned_paragraphs.append(buffer)
    return cleaned_paragraphs