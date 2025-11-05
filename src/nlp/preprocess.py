"""preprocess.py
Text cleaning and normalization utilities (spaCy, regex, sentence splitting).
"""
import spacy

# Load a small model by default; change to fr_core_news_sm or similar
try:
    nlp = spacy.load("fr_core_news_sm")
except Exception:
    nlp = spacy.blank("fr")

def clean_text(text: str) -> str:
    doc = nlp(text)
    sent_text = "\n".join([sent.text.strip() for sent in doc.sents])
    return sent_text
