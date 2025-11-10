"""
Ce script définit le backend de l'application (FastAPI).

Il expose un endpoint principal (`/run-etl`) qui permet à l'interface
utilisateur (Streamlit) de déclencher le pipeline ETL complet de manière
synchrone.

L'API attend que le pipeline (run_local_pipeline) soit terminé avant
de renvoyer une réponse (succès ou échec) au frontend.
"""

import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
import logging

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

try:
    from src.etl.dag_try import run_local_pipeline
except ImportError as e:
    print(f"Erreur d'import 'run_local_pipeline' dans FastAPI: {e}")
    def run_local_pipeline(type_doc: str, numero_doc: str):
        logging.error(f"ERREUR: run_local_pipeline n'a pas pu être importé.")
        return False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI(
    title="DocuExtract Backend",
    description="Gère le pipeline ETL de manière synchrone."
)

@app.post("/run-etl")
async def trigger_etl_synchronous(type_doc: str, numero_doc: str):
    """
    Déclenche le pipeline ETL complet et ATTEND sa complétion.
    """
    if not (type_doc and numero_doc):
        raise HTTPException(status_code=400, detail="type_doc et numero_doc sont requis")

    logger.info(f"[FastAPI] Tâche ETL SYNCHRONE démarrée pour: {type_doc}/{numero_doc}")
    
    try:
        success = run_local_pipeline(type_doc, numero_doc)
        
        if success:
            logger.info(f"[FastAPI] Tâche ETL SYNCHRONE RÉUSSIE pour: {type_doc}/{numero_doc}")
            return {
                "status": "success", 
                "message": f"ETL complété pour {type_doc}/{numero_doc}."
            }
        else:
            logger.error(f"[FastAPI] Tâche ETL SYNCHRONE ÉCHOUÉE pour: {type_doc}/{numero_doc}")
            raise HTTPException(status_code=500, detail="Le pipeline ETL a échoué.")
            
    except Exception as e:
        logger.error(f"[FastAPI] Exception dans la tâche ETL: {e}")
        raise HTTPException(status_code=500, detail=f"Erreur interne durant l'ETL: {e}")

@app.get("/")
def read_root():
    return {"message": "Serveur ETL DocuExtract Backend (Synchrone) est opérationnel."}