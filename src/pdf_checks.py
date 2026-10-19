"""Checks on the finished PDF (RT-005): page count and text read-back."""
import io
import re

from pypdf import PdfReader

# The fields src/resume.typ prints. A dict is a table (or a list of tables),
# None is a plain value or list of strings. Top-level tables not listed here
# are ignored by the template on purpose; unknown fields inside a listed
# table are reported, because the template would silently drop them.
FIELDS = {
    "contact": {"name": None, "location": None, "email": None, "phone": None, "links": None},
    "experience": {
        "company": None,
        "location": None,
        "roles": {"title": None, "dates": None, "bullets": None},
    },
    "projects": {"name": None, "dates": None, "bullets": None},
    "leadership": {"organization": None, "role": None, "dates": None, "bullets": None},
    "education": {"school": None, "location": None, "degree": None, "dates": None, "details": None},
    "skills": {"category": None, "items": None},
    "certifications": None,
}

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


def _split(data, fields, path, unprinted):
    """Collect the printed part of data and the dotted names of unknown fields."""
    if fields is None:
        return data
    if isinstance(data, list):
        return [_split(item, fields, path, unprinted) for item in data]
    if not isinstance(data, dict):
        return data
    kept = {}
    for key, value in data.items():
        if key in fields:
            kept[key] = _split(value, fields[key], f"{path}.{key}", unprinted)
        else:
            unprinted.append(f"{path}.{key}")
    return kept


def check_pdf(pdf_bytes, data):
    """Return (pages, missing, unprinted).

    missing: strings from printed fields that are not in the PDF text.
    unprinted: dotted names of fields the template does not print.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    text = _squash("".join(page.extract_text() for page in reader.pages))
    unprinted = []
    printed = {
        key: _split(data[key], fields, key, unprinted)
        for key, fields in FIELDS.items()
        if key in data
    }
    missing = [s for s in strings(printed) if _squash(s) not in text]
    return len(reader.pages), missing, unprinted
