"""
Ce script sert de point d'entrée pour exécuter le pipeline ETL complet
localement (sans Airflow) pour un seul document.

Il orchestre séquentiellement les étapes suivantes :
0. Setup DB: Initialise la connexion et les tables de la base de données.
1. Collecte: Télécharge le fichier PDF source.
2. Extraction: Applique l'OCR sur le PDF pour obtenir un fichier texte.
3. Transformation: Utilise l'IA pour convertir le texte en JSON structuré.
4. Chargement: Insère le JSON structuré dans la base de données PostgreSQL.

Ce script est conçu pour être exécuté directement (ex: python3 -m src.etl.dag_try)
à des fins de test ou de débogage du pipeline complet.
"""

import sys
import logging
from typing import Literal

from src.etl.collect import telecharger_document_benin 
from src.etl.extract import extract_layout_aware_text_ocr
from src.etl.transform import transform_text_to_json
from src.etl.load import load_single_document
from src.db.utils import initialize_db, get_db_engine

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

DocumentType = Literal["decrets", "loi", "ordonnance", "arrete", "accords", "decision"]

def setup_database() -> bool:
    """Initialise la base de données (crée/vérifie les tables)."""
    logger.info("Étape 0/5: Initialisation de la base de données...")
    try:
        engine = get_db_engine()
        initialize_db(engine)
        logger.info("Initialisation de la DB réussie.")
        return True
    except Exception as e:
        logger.error(f"Échec de l'initialisation de la DB: {e}", exc_info=False)
        return False

def run_local_pipeline(type_doc: DocumentType, numero_doc: str) -> bool:
    """
    Lance séquentiellement les cinq étapes du pipeline ETL pour un document donné.
    """
    logger.info(f"*** Démarrage du Pipeline ETL pour : {type_doc}/{numero_doc} ***")
    
    if not setup_database():
        logger.error("Le setup de la DB a échoué. Arrêt du pipeline.")
        return False

    logger.info("Étape 1/5: Collecte du PDF...")
    pdf_path = telecharger_document_benin(numero=numero_doc, type_doc=type_doc)
    
    if not pdf_path:
        logger.error("La collecte a échoué. Arrêt du pipeline.")
        return False
        
    logger.info(f"Collecte réussie. Fichier: {pdf_path}")
    
    logger.info("Étape 2/5: Extraction du texte brut (OCR/PyMuPDF)...")
    extraction_success = extract_layout_aware_text_ocr(type_doc=type_doc, numero=numero_doc)
    
    if not extraction_success:
        logger.error("L'extraction de texte a échoué. Arrêt du pipeline.")
        return False
        
    logger.info("Extraction de texte réussie.")

    logger.info("Étape 3/5: Transformation en JSON structuré (IA Gemini)...")
    transform_success = transform_text_to_json(type_doc=type_doc, numero=numero_doc)
    
    if not transform_success:
        logger.error("La transformation JSON a échoué. Arrêt du pipeline.")
        return False
        
    logger.info("Transformation JSON réussie.")

    logger.info("Étape 4/5: Chargement dans PostgreSQL...")
    load_success = load_single_document(type_doc=type_doc, numero_doc=numero_doc)
    
    if not load_success:
        logger.error("Le chargement dans la DB a échoué.")
        return False

    logger.info("Chargement dans la DB réussi.")
    logger.info(f"*** Pipeline ETL COMPLÉTÉ avec succès pour {type_doc}/{numero_doc}! ***")
    return True


if __name__ == "__main__":
    TYPE_TEST = "decret"
    NUMERO_TEST = "2025-652"
    
    logger.warning("NOTE: Assurez-vous d'avoir effacé les tables DB avant de relancer un test propre si le chargement a déjà réussi (pour éviter les doublons).")

    if run_local_pipeline(type_doc=TYPE_TEST, numero_doc=NUMERO_TEST):
        sys.exit(0)
    else:
        sys.exit(1)