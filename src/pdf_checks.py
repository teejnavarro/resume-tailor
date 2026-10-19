"""Checks on the finished PDF (RT-005): page count and text read-back."""
import io
import re

from pypdf import PdfReader

QUOTES = str.maketrans({"\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"'})


def _squash(text):
    return re.sub(r"\s+", "", text.translate(QUOTES))


def strings(data):
    """Every string value in the source data, in order (keys are skipped)."""
    if isinstance(data, str):
        yield data
    elif isinstance(data, dict):
        for value in data.values():
            yield from strings(value)
    elif isinstance(data, list):
        for item in data:
            yield from strings(item)


def check_pdf(pdf_bytes, data):
    """Return (pages, missing): page count and source strings not found in the text."""
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = _squash("".join(page.extract_text() for page in reader.pages))
    missing = [s for s in strings(data) if _squash(s) not in text]
    return len(reader.pages), missing
