"""utils.py
Database helper functions.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

def get_engine():
    user = os.getenv("DB_USER", "admin")
    pw = os.getenv("DB_PASSWORD", "changeme")
    host = os.getenv("DB_HOST", "localhost")
    db = os.getenv("DB_NAME", "docuextract")
    return create_engine(f"postgresql://{user}:{pw}@{host}/{db}")

def get_session():
    engine = get_engine()
    return sessionmaker(bind=engine)()
