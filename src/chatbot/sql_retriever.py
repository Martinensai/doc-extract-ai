"""
Ce script est le "Retriever" (récupérateur) pour le chatbot.
Il fait le lien entre l'application (Streamlit) et la base de données SQL.

Sa fonction principale, `get_document_context`, prend un type et un numéro
de document, interroge la base de données (table 'decrets' et ses relations),
et formate toutes les informations (objet, articles, signataires) en une
seule chaîne de caractères.

Cette chaîne sert ensuite de contexte (RAG) pour le LLM (Gemini).
"""

import sys
from pathlib import Path
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.orm.exc import NoResultFound

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

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
    
    session_gen = get_db_session()
    session = next(session_gen)
    
    context_parts = []
    
    try:
        decret = session.query(Decret).filter(
            Decret.type_document == type_doc,
            Decret.numero_complet == numero_doc
        ).one()

        context_parts.append(f"DOCUMENT: {decret.type_document} N° {decret.numero_complet}")
        context_parts.append(f"Date de publication: {decret.date_publication.strftime('%d %B %Y')}")
        context_parts.append(f"Ministère: {decret.ministere_concerne}")
        context_parts.append(f"Objet: {decret.objet}\n")
        
        context_parts.append("--- ARTICLES ---")
        if decret.articles:
            for article in decret.articles:
                context_parts.append(f"Article {article.numero_article}: {article.contenu}")
        else:
            context_parts.append("Aucun article trouvé pour ce document.")
        
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
        session.close()

if __name__ == "__main__":
    print("Test de la fonction get_document_context...")
    TYPE_TEST = "decret"
    NUMERO_TEST = "2025-652" 
    
    context = get_document_context(TYPE_TEST, NUMERO_TEST)
    print("="*30)
    print(context)
    print("="*30)