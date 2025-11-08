import sys
from pathlib import Path
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound

# --- Configuration des imports ---
# Ajoute le dossier racine (votre_projet/) au path
# pour que 'src' soit trouvable
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
# --- Fin Configuration des imports ---

try:
    from src.db.utils import get_db_session
    from src.db.models import Decret, DecretArticle, DecretSignataire
except ImportError as e:
    print(f"Erreur d'importation (sql_retriever.py): {e}")
    print("Assurez-vous que le script est exécuté depuis la racine ou que 'src' est dans PYTHONPATH.")
    sys.exit(1)

def get_document_context(type_doc: str, numero_doc: str) -> str:
    """
    Fetches a document and its related articles/signatories from the SQL database
    and formats them into a single string (context) for the LLM.
    """
    
    # Utilise le générateur de session de votre module utils.py
    session_gen = get_db_session()
    session = next(session_gen)
    
    context_parts = []
    
    try:
        # 1. Find the main document
        # NOTE: 'type_document' est le nom de la colonne dans votre models.py
        decret = session.query(Decret).filter(
            Decret.type_document == type_doc,
            Decret.numero_complet == numero_doc
        ).one()

        # 2. Build the context string
        context_parts.append(f"DOCUMENT: {decret.type_document} N° {decret.numero_complet}")
        context_parts.append(f"Date de publication: {decret.date_publication.strftime('%d %B %Y')}")
        context_parts.append(f"Ministère: {decret.ministere_concerne}")
        context_parts.append(f"Objet: {decret.objet}\n")
        
        # 3. Add Articles (using the relationship)
        context_parts.append("--- ARTICLES ---")
        if decret.articles:
            for article in decret.articles:
                context_parts.append(f"Article {article.numero_article}: {article.contenu}")
        else:
            context_parts.append("Aucun article trouvé pour ce document.")
        
        # 4. Add Signatories (using the relationship)
        context_parts.append("\n--- SIGNATAIRES ---")
        if decret.signataires:
            for sig in decret.signataires:
                context_parts.append(f"- {sig.nom_signataire} ({sig.fonction_signataire})")
        else:
            context_parts.append("Aucun signataire trouvé.")

        return "\n".join(context_parts)

    except NoResultFound:
        return f"Erreur: Le document {type_doc}/{numero_doc} n'a pas été trouvé dans la base de données."
    except Exception as e:
        return f"Erreur de base de données: {e}"
    finally:
        # 5. Always close the session
        session.close()

if __name__ == "__main__":
    # Test function
    print("Test de la fonction get_document_context...")
    # Assurez-vous que ce document existe dans votre DB locale
    TYPE_TEST = "decret"
    NUMERO_TEST = "2025-652" 
    
    context = get_document_context(TYPE_TEST, NUMERO_TEST)
    print("="*30)
    print(context)
    print("="*30)