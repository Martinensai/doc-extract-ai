import locale
from typing import Optional, Dict, Any, List
import os
import json
import logging
from pathlib import Path
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import Dict, Any, List

# Importation des modules locaux
from ..db.models  import Decret, DecretArticle, DecretSignataire
from ..db.utils import get_db_session

# Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Définition du chemin de base des données structurées
BASE_STRUCTURED_PATH = Path("data/extracted")

def format_date(date_str: str) -> Optional[datetime.date]:
    """
    Convertit la date de publication du format texte français au format datetime.date,
    en forçant l'utilisation de la locale française.
    """
    # Force l'utilisation de la locale française pour que "octobre" soit reconnu.
    # On essaie d'abord fr_FR.UTF-8, puis juste fr_FR
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR')
        except locale.Error:
            # Si aucune locale française n'est trouvée (très rare sur Ubuntu)
            logger.warning("Locale 'fr_FR' non disponible. Le parsing risque d'échouer.")
            
    # Format: %d (jour), %B (Nom complet du mois dans la locale), %Y (année complète)
    DATE_FORMAT = "%d %B %Y"
    
    try:
        dt_object = datetime.strptime(date_str, DATE_FORMAT)
        return dt_object.date()
    except Exception as e:
        # Ne pas logger l'erreur ici car le WARNING est déjà géré en amont
        return None

def load_single_document(type_doc: str, numero_doc: str) -> bool:
    """
    Charge les données structurées d'un seul document spécifique (JSON) dans la base de données.
    
    Args:
        type_doc (str): Le type de document ('decret', 'loi', etc.)
        numero_doc (str): Le numéro complet du document (ex: '2025-652').

    Returns:
        bool: True si le chargement a réussi, False sinon.
    """
    logger.info(f"\n--- Démarrage du chargement pour {type_doc}/{numero_doc} ---")
    
    # 1. Construction du chemin du fichier JSON
    json_file_path = BASE_STRUCTURED_PATH / type_doc / f"{numero_doc}.json"
    
    if not json_file_path.exists():
        logger.error(f"❌ Fichier JSON non trouvé: {json_file_path}")
        logger.error("Veuillez vous assurer que la phase de transformation (T) a créé ce fichier.")
        return False
        
    # 2. Lecture du fichier JSON
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"❌ Erreur de décodage JSON dans {json_file_path.name}. Fichier corrompu.")
        return False
    
    # 3. Traitement et insertion dans la base de données
    
    # Nous utilisons le générateur de session de db/utils.py
    for session in get_db_session():
        # Utilisation d'un bloc try/finally pour garantir la gestion de la session
        try:
            # Vérification anti-doublon (utilise le numéro unique comme clé)
            existing_decret = session.query(Decret).filter_by(numero_complet=numero_doc).first()

            if existing_decret:
                logger.warning(f"Décret {numero_doc} existe déjà. Insertion annulée.")
                return True
            
            # --- 3.1. Préparation des données ---
            date_str = json_data.get("date_de_publication", "")
            date_obj = format_date(date_str)
            
            if not date_obj:
                logger.error(f"Abandon du chargement: Date manquante ou invalide ({date_str}).")
                return False

            # --- 3.2. Création de l'objet DECRET principal ---
            nouveau_decret = Decret(
                numero_complet=json_data.get("numéro_du_décret"),
                type_document=type_doc,
                date_publication=date_obj,
                ministere_concerne=json_data.get("ministère_concerné"),
                objet=json_data.get("objet"),
                # Chemin vers le fichier RAW (nécessaire pour la traçabilité)
                chemin_fichier_local=str(Path("data/raw") / type_doc / f"{numero_doc}.pdf")
            )
            
            # --- 3.3. Ajout des ARTICLES et SIGNATAIRES (Relations) ---
            
            # Articles (Assurez-vous que l'IA retourne une liste d'objets Articles)
            articles: List[Dict] = json_data.get("articles", [])
            for art in articles:
                nouveau_decret.articles.append(
                    DecretArticle(
                        numero_article=art.get("numero"),
                        contenu=art.get("texte")
                    )
                )

            # Signataires
            signataires: List[Dict] = json_data.get("signataires", [])
            for sign in signataires:
                nouveau_decret.signataires.append(
                    DecretSignataire(
                        nom_signataire=sign.get("nom"),
                        fonction_signataire=sign.get("fonction")
                    )
                )

            # --- 3.4. Finalisation de la transaction ---
            session.add(nouveau_decret)
            session.commit()
            logger.info(f"✅ Chargement de {type_doc}/{numero_doc} réussi.")
            return True

        except IntegrityError as e:
            session.rollback() 
            logger.error(f"❌ Erreur d'intégrité (doublon ou contrainte non respectée): {e}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Erreur lors de l'insertion du document: {e}")
            return False

# --- Exemple d'utilisation (pour tester) ---
if __name__ == "__main__":
    # Paramètres de test : Doivent correspondre à votre fichier JSON
    TYPE_TEST = "decret"
    NUMERO_TEST = "2025-652"
    
    # NOTE: Ce script dépend de la présence du fichier JSON :
    # data/structured/decret/2025-652.json
    
    # Pour tester, assurez-vous que vous avez exécuté les étapes de configuration DB
    if load_single_document(type_doc=TYPE_TEST, numero_doc=NUMERO_TEST):
         logger.info(f"Chargement terminé pour {TYPE_TEST}/{NUMERO_TEST}.")
    else:
         logger.error(f"Échec du chargement pour {TYPE_TEST}/{NUMERO_TEST}.")