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

# --- Configuration des imports ---
import sys
from pathlib import Path
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
# --- Fin Configuration des imports ---

try:
    from src.db.models  import Decret, DecretArticle, DecretSignataire
    from src.db.utils import get_db_session
except ImportError:
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
    try:
        locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR')
        except locale.Error:
            logger.warning("Locale 'fr_FR' non disponible. Le parsing risque d'échouer.")
            
    DATE_FORMAT = "%d %B %Y"
    
    try:
        dt_object = datetime.strptime(date_str, DATE_FORMAT)
        return dt_object.date()
    except Exception as e:
        return None

def load_single_document(type_doc: str, numero_doc: str) -> bool:
    """
    Charge les données structurées d'un seul document spécifique (JSON) dans la base de données.
    (Version auto-nettoyante)
    """
    logger.info(f"\n--- Démarrage du chargement pour {type_doc}/{numero_doc} ---")
    
    json_file_path = BASE_STRUCTURED_PATH / type_doc / f"{numero_doc}.json"
    
    if not json_file_path.exists():
        logger.error(f"❌ Fichier JSON non trouvé: {json_file_path}")
        return False
        
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except json.JSONDecodeError:
        logger.error(f"❌ Erreur de décodage JSON dans {json_file_path.name}. Fichier corrompu.")
        return False
    
    for session in get_db_session():
        try:
            # 1. Vérification par 'numero_complet' (Cas normal)
            existing_decret = session.query(Decret).filter_by(numero_complet=numero_doc).first()
            if existing_decret:
                logger.warning(f"Décret {numero_doc} existe déjà (par numéro). Insertion annulée.")
                return True
            
            # 2. Vérification "auto-nettoyante" par 'chemin_fichier_local' (Cas du bug)
            chemin_pdf = str(Path("data/raw") / type_doc / f"{numero_doc}.pdf")
            ghost_entry = session.query(Decret).filter_by(chemin_fichier_local=chemin_pdf).first()
            
            if ghost_entry:
                logger.warning(f"Conflit de chemin détecté pour {chemin_pdf}.")
                logger.warning(f"Suppression de l'entrée 'fantôme' (ID: {ghost_entry.id_decret}, Num: {ghost_entry.numero_complet}).")
                session.delete(ghost_entry)
                session.commit() # Commit de la suppression
            
            # --- 3. Insertion (la voie est libre) ---
            date_str = json_data.get("date_de_publication", "")
            date_obj = format_date(date_str)
            
            if not date_obj:
                logger.error(f"Abandon du chargement: Date manquante ou invalide ({date_str}).")
                return False

            nouveau_decret = Decret(
                numero_complet=numero_doc, # Utilise le numéro correct
                type_document=type_doc,
                date_publication=date_obj,
                ministere_concerne=json_data.get("ministère_concerné"),
                objet=json_data.get("objet"),
                chemin_fichier_local=chemin_pdf # Utilise le chemin construit
            )
            
            articles: List[Dict] = json_data.get("articles", [])
            for art in articles:
                nouveau_decret.articles.append(
                    DecretArticle(
                        numero_article=art.get("numero"),
                        contenu=art.get("texte")
                    )
                )

            signataires: List[Dict] = json_data.get("signataires", [])
            for sign in signataires:
                nouveau_decret.signataires.append(
                    DecretSignataire(
                        nom_signataire=sign.get("nom"),
                        fonction_signataire=sign.get("fonction")
                    )
                )

            session.add(nouveau_decret)
            session.commit()
            logger.info(f"✅ Chargement de {type_doc}/{numero_doc} réussi.")
            return True

        except IntegrityError as e:
            session.rollback() 
            logger.error(f"❌ Erreur d'intégrité (non gérée): {e}")
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Erreur lors de l'insertion du document: {e}")
            return False

# ... (le if __name__ == "__main__" reste inchangé) ...
if __name__ == "__main__":
    TYPE_TEST = "decret"
    NUMERO_TEST = "2025-652"
    if load_single_document(type_doc=TYPE_TEST, numero_doc=NUMERO_TEST):
         logger.info(f"Chargement terminé pour {TYPE_TEST}/{NUMERO_TEST}.")
    else:
         logger.error(f"Échec du chargement pour {TYPE_TEST}/{NUMERO_TEST}.")