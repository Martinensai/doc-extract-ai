"""extract.py
Extract text from PDFs using PyMuPDF (fitz).
"""
import fitz  # PyMuPDF
from pathlib import Path

RAW_DIR = Path("data/raw")
EXTRACTED_DIR = Path("data/extracted")
EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)

def extract_text_from_pdf(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    text = []
    for page in doc:
        text.append(page.get_text())
    return "\n".join(text)

def run_all():
    for pdf in RAW_DIR.glob("*.pdf"):
        txt = extract_text_from_pdf(pdf)
        out = EXTRACTED_DIR / (pdf.stem + ".txt")
        out.write_text(txt, encoding="utf-8")
        print(f"Extracted {pdf} -> {out}")

if __name__ == '__main__':
    run_all()
