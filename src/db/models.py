"""models.py
SQLAlchemy ORM models (if you prefer ORM over raw SQL).
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, func

Base = declarative_base()

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True)
    title = Column(String(512))
    metadata = Column(JSON)
    content = Column(Text)
    created_at = Column(DateTime, default=func.now())
