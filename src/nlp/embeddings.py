"""embeddings.py
Create embeddings for documents using sentence-transformers or Hugging Face.
"""
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"  # choose a FR-friendly model if needed

def get_model(name=MODEL_NAME):
    return SentenceTransformer(name)

def embed_texts(texts):
    model = get_model()
    return model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
