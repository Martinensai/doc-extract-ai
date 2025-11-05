"""config.py
Configuration centralisée pour chemins, modèles et paramètres.
"""
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
EXTRACTED_DIR = BASE_DIR / "data" / "extracted"
STRUCTURED_DIR = BASE_DIR / "data" / "structured"
