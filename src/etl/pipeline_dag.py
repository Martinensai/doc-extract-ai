"""pipeline_dag.py
Skeleton Airflow DAG that would orchestrate the ETL steps.
Place this file in the Airflow DAGs folder or point Airflow to src/etl.
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

default_args = {
    "owner": "docuextract",
    "depends_on_past": False,
    "start_date": datetime(2025,1,1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

def collect_task():
    from src.etl import collect
    collect.main()

def extract_task():
    from src.etl import extract
    extract.run_all()

def transform_task():
    from src.etl import transform
    transform.run_all()

def load_task():
    from src.etl import load
    load.load_all()

with DAG("docuextract_pipeline", default_args=default_args, schedule_interval="@daily", catchup=False) as dag:
    t1 = PythonOperator(task_id="collect", python_callable=collect_task)
    t2 = PythonOperator(task_id="extract", python_callable=extract_task)
    t3 = PythonOperator(task_id="transform", python_callable=transform_task)
    t4 = PythonOperator(task_id="load", python_callable=load_task)

    t1 >> t2 >> t3 >> t4
