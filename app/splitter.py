from __future__ import annotations

import re
from typing import List


def split_text(text: str, min_chars: int = 400, max_chars: int = 700) -> List[str]:
    # Simple sentence-aware chunker
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: List[str] = []
    buf: List[str] = []
    total = 0
    for s in sentences:
        s = s.strip()
        if not s:
            continue
        if total + len(s) + (1 if buf else 0) <= max_chars:
            buf.append(s)
            total += len(s) + (1 if buf else 0)
        else:
            if total >= min_chars or not buf:
                if buf:
                    chunks.append(" ".join(buf))
                buf = [s]
                total = len(s)
            else:
                # force split
                chunks.append(" ".join(buf))
                buf = [s]
                total = len(s)
    if buf:
        chunks.append(" ".join(buf))
    return [c.strip() for c in chunks if c.strip()]

