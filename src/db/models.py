from sqlalchemy import Column, Integer, String, Text, Date, ForeignKey
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.schema import UniqueConstraint

# Classe de base pour l'ORM SQLAlchemy
class Base(DeclarativeBase):
    pass

class Decret(Base):
    __tablename__ = 'decrets'

    id_decret = Column(Integer, primary_key=True)
    numero_complet = Column(String(50), nullable=False, unique=True)
    type_document = Column(String(20), nullable=False)
    date_publication = Column(Date, nullable=False)
    ministere_concerne = Column(String(255), nullable=False)
    objet = Column(Text, nullable=False)
    checksum = Column(String(64), unique=True)
    chemin_fichier_local = Column(String(500), nullable=False, unique=True)

    # Relations (pour les jointures automatiques)
    articles = relationship("DecretArticle", back_populates="decret", cascade="all, delete-orphan")
    signataires = relationship("DecretSignataire", back_populates="decret", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Decret(num='{self.numero_complet}', obj='{self.objet[:30]}...')>"

class DecretArticle(Base):
    __tablename__ = 'decret_articles'

    id_article = Column(Integer, primary_key=True)
    id_decret = Column(Integer, ForeignKey('decrets.id_decret'), nullable=False)
    numero_article = Column(String(20), nullable=False)
    contenu = Column(Text, nullable=False)

    __table_args__ = (
        UniqueConstraint('id_decret', 'numero_article', name='uq_decret_article'),
    )
    decret = relationship("Decret", back_populates="articles")

    def __repr__(self):
        return f"<DecretArticle(num='{self.numero_article}')>"

class DecretSignataire(Base):
    __tablename__ = 'decret_signataires'

    id_signature = Column(Integer, primary_key=True)
    id_decret = Column(Integer, ForeignKey('decrets.id_decret'), nullable=False)
    nom_signataire = Column(String(150), nullable=False)
    fonction_signataire = Column(String(255), nullable=False)

    __table_args__ = (
        UniqueConstraint('id_decret', 'nom_signataire', name='uq_decret_signataire'),
    )
    decret = relationship("Decret", back_populates="signataires")

    def __repr__(self):
        return f"<DecretSignataire(nom='{self.nom_signataire}')>"