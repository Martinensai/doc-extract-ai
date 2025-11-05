"""transform.py
Parse and structure extracted texts. This is a template to detect dates, signatories, etc.
"""
import re
from pathlib import Path
import json

EXTRACTED_DIR = Path("data/extracted")
STRUCTURED_DIR = Path("data/structured")
STRUCTURED_DIR.mkdir(parents=True, exist_ok=True)

def parse_document(text: str) -> dict:
    # naive examples: replace with robust NLP rules
    date_match = re.search(r"(\d{1,2} \w+ \d{4})", text)
    date = date_match.group(0) if date_match else None
    title = text.strip().splitlines()[0] if text.strip() else None
    # TODO: extract ministry, signatory, object, decree number, etc.
    return {"title": title, "date": date, "text_snippet": text[:500]}

def run_all():
    for txt_file in EXTRACTED_DIR.glob("*.txt"):
        text = txt_file.read_text(encoding="utf-8")
        record = parse_document(text)
        out = STRUCTURED_DIR / (txt_file.stem + ".json")
        out.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Structured {txt_file} -> {out}")

if __name__ == '__main__':
    run_all()
