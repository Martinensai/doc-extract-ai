from __future__ import annotations

import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# --- Importation des fonctions Python ---
# NOTE: Ces imports nécessitent que le dossier 'src' soit dans le PYTHONPATH 
# ou que ce DAG soit exécuté dans un environnement Airflow qui connaît 'src'.

# Supposons ces imports pour la démonstration:
from src.etl.collect import telecharger_document_benin
from src.etl.extract import extract_layout_aware_text_ocr
from src.etl.transform import transform_text_to_json
from src.etl.load import load_single_document

# --- Définition des Paramètres du Pipeline (Paramètres du DAG) ---
# En production, ces valeurs seraient souvent passées via une variable Airflow 
# ou un déclencheur de DAG. Pour la simplicité ici, nous les définissons.

DEFAULT_TYPE = "decret"
DEFAULT_NUMERO = "2025-652"

with DAG(
    dag_id="docuextract_benin_full_pipeline",
    start_date=days_ago(1),
    schedule=None, # Exécution manuelle (manually triggered)
    catchup=False,
    tags=["etl", "llm", "doc-extract"],
    default_args={
        "owner": "airflow",
        "depends_on_past": False,
        "email_on_failure": False,
        "email_on_retry": False,
        "retries": 1,
    }
) as dag:
    
    # --- 1. Tâche de Collecte (E1) ---
    task_collect = PythonOperator(
        task_id="collect_pdf_document",
        python_callable=telecharger_document_benin,
        op_kwargs={
            "type_doc": DEFAULT_TYPE,
            "numero": DEFAULT_NUMERO,
        },
    )

    # --- 2. Tâche d'Extraction (E2) ---
    task_extract = PythonOperator(
        task_id="extract_text_from_pdf",
        python_callable=extract_layout_aware_text_ocr,
        op_kwargs={
            "type_doc": DEFAULT_TYPE,
            "numero": DEFAULT_NUMERO,
        },
    )
    
    # --- 3. Tâche de Transformation (T) ---
    task_transform = PythonOperator(
        task_id="transform_to_structured_json",
        python_callable=transform_text_to_json,
        op_kwargs={
            "type_doc": DEFAULT_TYPE,
            "numero": DEFAULT_NUMERO,
        },
    )

    # --- 4. Tâche de Chargement (L) ---
    task_load = PythonOperator(
        task_id="load_data_to_postgres",
        python_callable=load_single_document,
        op_kwargs={
            "type_doc": DEFAULT_TYPE,
            "numero_doc": DEFAULT_NUMERO, # Note: Utilise numero_doc comme nom d'argument dans load.py
        },
    )

    # --- Définition de la SÉQUENCE ---
    # La flèche (>>) garantit que la tâche suivante ne commence que si la précédente a réussi.
    task_collect >> task_extract >> task_transform >> task_load