import os
import logging
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

# --- Configuration ---
load_dotenv()
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
SCHEMA_FILE_PATH = os.path.join(os.path.dirname(__file__), "schema.sql")

def get_database_url() -> str:
    """Construit l'URL de connexion à la base de données locale."""
    if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
        raise EnvironmentError("Variables de connexion DB manquantes. Vérifiez le fichier .env.")
        
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def get_db_engine() -> Engine:
    """Crée l'objet Engine de SQLAlchemy."""
    db_url = get_database_url()
    # pool_pre_ping=True est utile pour les connexions Docker
    return create_engine(db_url, pool_pre_ping=True)

def initialize_db(engine: Engine):
    """Exécute le script schema.sql pour créer ou vérifier les tables."""
    try:
        with open(SCHEMA_FILE_PATH, 'r') as f:
            sql_script = f.read()
        
        with engine.connect() as connection:
            # Exécute tout le script SQL
            connection.execute(text(sql_script))
            connection.commit()
        
        logger.info("✅ Schéma de la base de données créé/vérifié avec succès.")

    except FileNotFoundError:
        logger.error(f"❌ Fichier de schéma non trouvé : {SCHEMA_FILE_PATH}")
        raise
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'initialisation de la DB. Le conteneur Docker est-il démarré ? : {e}")
        raise

# --- Utilisation typique dans le Pipeline ETL (pour obtenir une session de travail) ---
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_db_engine())

def get_db_session():
    """Générateur pour obtenir une session de DB, utilisée dans les fonctions d'insertion."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

# --- Test d'initialisation ---
if __name__ == '__main__':
    try:
        engine = get_db_engine()
        initialize_db(engine)
    except Exception:
        print("\n\nATTENTION : L'initialisation a échoué. Assurez-vous que le service 'db' est démarré :")
        print("   $ docker compose up -d")