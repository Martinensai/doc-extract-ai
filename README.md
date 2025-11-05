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
