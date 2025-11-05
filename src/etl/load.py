"""load.py
Load structured JSON records into PostgreSQL.
Uses SQLAlchemy for simplicity.
"""
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, Text
from sqlalchemy.dialects.postgresql import JSONB
import os
import json
from pathlib import Path

STRUCTURED_DIR = Path("data/structured")

def get_engine():
    user = os.getenv("DB_USER", "admin")
    pw = os.getenv("DB_PASSWORD", "changeme")
    host = os.getenv("DB_HOST", "localhost")
    db = os.getenv("DB_NAME", "docuextract")
    url = f"postgresql://{user}:{pw}@{host}/{db}"
    return create_engine(url)

def ensure_table(engine):
    meta = MetaData()
    documents = Table(
        "documents", meta,
        Column("id", Integer, primary_key=True),
        Column("title", String(512)),
        Column("metadata", JSONB),
        Column("content", Text)
    )
    meta.create_all(engine)

def load_all():
    engine = get_engine()
    ensure_table(engine)
    for j in STRUCTURED_DIR.glob("*.json"):
        data = json.loads(j.read_text(encoding='utf-8'))
        # TODO: insert into DB (use SQLAlchemy core or ORM)
        print("Would insert:", j.name, data.get("title"))

if __name__ == '__main__':
    load_all()
