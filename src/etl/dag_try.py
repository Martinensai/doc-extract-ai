import sys
import logging
from typing import Literal

# --- 1. Importations des Fonctions ETL ---
# NOTE: Ces imports nécessitent que le dossier 'src' soit configuré dans votre PYTHONPATH
# ou que vous utilisiez la structure d'importation relative corrigée (non recommandée ici).

# Exemple d'imports basé sur la structure du DAG et les noms de fonctions
# Vous devrez peut-être ajuster ces chemins d'accès
from .collect import telecharger_document_benin 
from .extract import extract_layout_aware_text_ocr # Nom supposé pour l'extraction de texte
from .transform import transform_text_to_json
from .load import load_single_document

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Définition des types de documents valides (pour type hinting)
DocumentType = Literal["decrets", "loi", "ordonnance", "arrete", "accords", "decision"]


def run_local_pipeline(type_doc: DocumentType, numero_doc: str) -> bool:
    """
    Lance séquentiellement les quatre fonctions du pipeline ETL pour un document donné.
    
    Args:
        type_doc (DocumentType): Le type de document (ex: 'decrets').
        numero_doc (str): Le numéro complet du document (ex: '2025-652').

    Returns:
        bool: True si toutes les étapes réussissent, False sinon.
    """
    logger.info(f"*** Démarrage du Pipeline ETL pour : {type_doc}/{numero_doc} ***")
    
    # ------------------------------------
    # TÂCHE 1 : COLLECTE (C)
    # ------------------------------------
    logger.info("Étape 1/4: Collecte du PDF...")
    # telecharger_document_benin retourne le chemin du fichier ou None (si échec)
    pdf_path = telecharger_document_benin(numero=numero_doc, type_doc=type_doc)
    
    if not pdf_path:
        logger.error("La collecte a échoué. Arrêt du pipeline.")
        return False
        
    logger.info(f"Collecte réussie. Fichier: {pdf_path}")
    
    # ------------------------------------
    # TÂCHE 2 : EXTRACTION (E)
    # ------------------------------------
    logger.info("Étape 2/4: Extraction du texte brut (OCR/PyMuPDF)...")
    # extract_layout_aware_text_ocr doit retourner True ou False
    extraction_success = extract_layout_aware_text_ocr(type_doc=type_doc, numero=numero_doc)
    
    if not extraction_success:
        logger.error("L'extraction de texte a échoué. Arrêt du pipeline.")
        return False
        
    logger.info("Extraction de texte réussie.")

    # ------------------------------------
    # TÂCHE 3 : TRANSFORMATION (T)
    # ------------------------------------
    logger.info("Étape 3/4: Transformation en JSON structuré (IA Gemini)...")
    # transform_text_to_json doit retourner True ou False
    transform_success = transform_text_to_json(type_doc=type_doc, numero=numero_doc)
    
    if not transform_success:
        logger.error("La transformation JSON a échoué. Arrêt du pipeline.")
        return False
        
    logger.info("Transformation JSON réussie.")

    # ------------------------------------
    # TÂCHE 4 : CHARGEMENT (L)
    # ------------------------------------
    logger.info("Étape 4/4: Chargement dans PostgreSQL...")
    # load_single_document doit retourner True ou False
    load_success = load_single_document(type_doc=type_doc, numero_doc=numero_doc)
    
    if not load_success:
        logger.error("Le chargement dans la DB a échoué.")
        return False

    logger.info("Chargement dans la DB réussi.")
    logger.info(f"*** Pipeline ETL COMPLÉTÉ avec succès pour {type_doc}/{numero_doc}! ***")
    return True


# --- Exécution du Pipeline de Test ---
if __name__ == "__main__":
    # Utilisez le décret que nous avons chargé manuellement pour le test L
    TYPE_TEST = "decret"
    NUMERO_TEST = "2025-652"
    
    if run_local_pipeline(type_doc=TYPE_TEST, numero_doc=NUMERO_TEST):
        sys.exit(0) # Sortie succès
    else:
        sys.exit(1) # Sortie échec