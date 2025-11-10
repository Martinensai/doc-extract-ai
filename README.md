# 🇧🇯 DocuExtract Benin

> **Extraction intelligente et interrogation des documents publics béninois**

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?logo=streamlit)
![AWS](https://img.shields.io/badge/AWS-Cloud-orange?logo=amazon-aws)
![Docker](https://img.shields.io/badge/Containerized-Docker-blue?logo=docker)
![LangChain](https://img.shields.io/badge/LangChain-AI-green?logo=openai)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🧭 Aperçu du projet

**DocuExtract Benin** est un projet open-source conçu pour automatiser l’extraction, la structuration et la recherche d’informations dans les **documents publics béninois** (décrets, arrêtés, communiqués officiels).

Le projet met en œuvre un **pipeline complet d’ingénierie des données** et une **interface IA** pour interroger les documents en langage naturel.

---

## 🎯 Objectifs

- 🧩 Collecter automatiquement les documents publics depuis les sites gouvernementaux.  
- 📄 Extraire et nettoyer les contenus textuels à partir de fichiers PDF.  
- 🧠 Identifier et structurer les métadonnées clés (date, signataire, ministère, objet du décret…).  
- 🗃️ Stocker les données structurées dans une base PostgreSQL.  
- 🔍 Indexer les textes pour la **recherche sémantique** avec embeddings.  
- 💬 Fournir une interface de **chatbot IA** pour interroger les décrets.

---

## 🧱 Architecture technique

```mermaid
flowchart TD
    A[📄 PDF officiels en ligne] --> B[☁️ AWS S3 - Stockage brut]
    B --> C[⚙️ Airflow / Lambda - Pipeline ETL]
    C --> D[(🗃️ PostgreSQL - Données structurées)]
    D --> E[🧮 ChromaDB / FAISS - Index vectoriel]
    E --> F[🤖 Chatbot LangChain + Streamlit]

## 🚀 Installation

1. Cloner le dépôt :
```bash
git clone https://github.com/Martinensai/doc-extract-ai.git
cd doc-extract-ai
```

2. Créer et activer un environnement virtuel :
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
```

3. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## 🗄️ Configuration de PostgreSQL

1. Installation de PostgreSQL :
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

2. Démarrer le service PostgreSQL :
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

3. Se connecter à PostgreSQL et créer une base de données :
```bash
sudo -u postgres psql
```

Dans l'invite PostgreSQL :
```sql
CREATE DATABASE docuextract;
CREATE USER docuextract_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE docuextract TO docuextract_user;
\c docuextract
```

4. Initialiser la base de données avec le schéma :
```bash
psql -U docuextract_user -d docuextract -f src/db/schema.sql
```

Pour supprimer les tables si nécessaire :
```sql
DROP TABLE IF EXISTS decret_signataires CASCADE;
DROP TABLE IF EXISTS decret_articles CASCADE;
DROP TABLE IF EXISTS decrets CASCADE;
```

## 🚀 Lancement de l'application

1. Lancer l'API FastAPI (dans un terminal) :
```bash
cd src/api
uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

L'API sera accessible à l'adresse : http://localhost:8000

2. Lancer l'interface Streamlit (dans un autre terminal) :
```bash
cd src/chatbot
streamlit run app.py
```

L'interface sera accessible à l'adresse : http://localhost:8501