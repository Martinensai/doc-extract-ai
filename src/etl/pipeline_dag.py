"""
Ce script définit un pipeline Airflow (DAG) pour orchestrer
le processus ETL complet d'extraction de documents.

Le pipeline est linéaire et exécute les 4 étapes principales :
1. Collect (Téléchargement du PDF via telecharger_document_benin)
2. Extract (OCR et extraction du texte via extract_layout_aware_text_ocr)
3. Transform (Conversion du texte en JSON structuré via transform_text_to_json)
4. Load (Chargement du JSON en base de données via load_single_document)

Ce DAG est conçu pour être déclenché manuellement (schedule=None) pour un
document spécifique (type_doc, numero).
"""

from __future__ import annotations

import pendulum
from airflow.models.dag import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

from src.etl.collect import telecharger_document_benin
from src.etl.extract import extract_layout_aware_text_ocr
from src.etl.transform import transform_text_to_json
from src.etl.load import load_single_document

DEFAULT_TYPE = "decret"
DEFAULT_NUMERO = "2025-652"

with DAG(
    dag_id="docuextract_benin_full_pipeline",
    start_date=days_ago(1),
    schedule=None,
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
    
    task_collect = PythonOperator(
        task_id="collect_pdf_document",
        python_callable=telecharger_document_benin,
        op_kwargs={
            "type_doc": DEFAULT_TYPE,
            "numero": DEFAULT_NUMERO,
        },
    )

    task_extract = PythonOperator(
        task_id="extract_text_from_pdf",
        python_callable=extract_layout_aware_text_ocr,
        op_kwargs={
            "type_doc": DEFAULT_TYPE,
            "numero": DEFAULT_NUMERO,
        },
    )
    
    task_transform = PythonOperator(
        task_id="transform_to_structured_json",
        python_callable=transform_text_to_json,
        op_kwargs={
            "type_doc": DEFAULT_TYPE,
            "numero": DEFAULT_NUMERO,
        },
    )

    task_load = PythonOperator(
        task_id="load_data_to_postgres",
        python_callable=load_single_document,
        op_kwargs={
            "type_doc": DEFAULT_TYPE,
            "numero_doc": DEFAULT_NUMERO,
        },
    )

    # Définition de la séquence des tâches
    task_collect >> task_extract >> task_transform >> task_load