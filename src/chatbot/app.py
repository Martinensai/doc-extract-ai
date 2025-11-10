"""
Ce script définit l'interface utilisateur (UI) de l'application Streamlit
pour "DocuExtract Benin".

Il permet à l'utilisateur de :
1.  Sélectionner un type de document et entrer un numéro (barre latérale).
2.  Charger le document. Si le document n'est pas dans la base de données,
    l'application appelle un backend FastAPI (sur BACKEND_URL) pour
    déclencher le pipeline ETL complet.
3.  Afficher le contexte du document chargé (colonne 1).
4.  Interagir avec un chatbot (alimenté par Gemini) qui répond aux
    questions sur la base du contexte du document chargé (colonne 2).
"""

import streamlit as st
import sys
from pathlib import Path
import requests

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from src.chatbot.sql_retriever import get_document_context
from src.chatbot.llm_handler import get_gemini_response 

st.set_page_config(page_title="DocuExtract Benin", layout="wide")
st.title("Assistant Documentaire - Bénin 🇧🇯")
st.markdown("Interrogez les documents officiels (décrets, lois, etc.)")

st.sidebar.header("1. Charger un Document")
DOC_TYPES = ["decret", "loi", "ordonnance", "decision", "arrete", "accord"]
type_doc = st.sidebar.selectbox(
    "Type de document", 
    DOC_TYPES,
    help="Sélectionnez le type de document que vous souhaitez analyser."
)
numero_doc = st.sidebar.text_input(
    "Numéro du document", 
    placeholder="ex: 2025-652",
    help="Entrez le numéro complet du document (ex: 2024-1051, 2025-652)."
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "document_context" not in st.session_state:
    st.session_state.document_context = None

col1, col2 = st.columns([1, 1])

BACKEND_URL = "http://localhost:8000/run-etl"

with col1:
    st.header("Document Actif")
    
    if st.sidebar.button("Charger le document"):
        if not numero_doc:
            st.sidebar.error("Veuillez entrer un numéro de document.")
        else:
            context = None
            
            with st.spinner(f"Recherche de {type_doc}/{numero_doc} dans la base de données..."):
                context = get_document_context(type_doc, numero_doc)
            
            if context.startswith("Erreur:") and "n'a pas été trouvé" in context:
                
                with st.spinner(f"Document non trouvé. Veuillez patienter (1-2 min)..."):
                    try:
                        response = requests.post(
                            BACKEND_URL,
                            params={"type_doc": type_doc, "numero_doc": numero_doc},
                            timeout=300 
                        )
                        
                        if response.status_code == 200:
                            with st.spinner("ETL terminé. Chargement du document..."):
                                context = get_document_context(type_doc, numero_doc)
                        else:
                            context = f"Erreur: Le pipeline ETL a échoué: {response.json().get('detail')}"

                    except requests.exceptions.ConnectionError:
                        context = "Erreur: Le backend FastAPI ne répond pas."
                    except requests.exceptions.ReadTimeout:
                        context = "Erreur: L'ETL a pris trop de temps (plus de 5 minutes)."
                    except Exception as e:
                        context = f"Erreur imprévue: {e}"

            if context.startswith("Erreur:"):
                st.error(context)
                st.session_state.document_context = None
                st.session_state.messages = [] 
            else:
                st.success(f"Document {type_doc}/{numero_doc} chargé !")
                st.session_state.document_context = context
                st.session_state.document_name = f"{type_doc}/{numero_doc}"
                st.session_state.messages = [{
                    "role": "assistant", 
                    "content": f"Bonjour ! Je suis prêt à répondre à vos questions sur le document {numero_doc}."
                }]

    if st.session_state.document_context:
        st.subheader(f"Détails pour : {st.session_state.document_name}")
        st.text_area(
            "Contenu du document", 
            st.session_state.document_context, 
            height=500
        )

with col2:
    st.header("Chatbot")
    
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("Posez votre question ici..."):
        if not st.session_state.document_context:
            st.error("Veuillez d'abord charger un document avant de poser une question.")
        else:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Réflexion..."):
                    response = get_gemini_response(
                        context=st.session_state.document_context,
                        chat_history=st.session_state.messages[:-1], 
                        user_question=prompt
                    )
                    st.markdown(response)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
    
    elif not st.session_state.document_context:
        st.info("Chargez un document dans la barre latérale pour commencer à chatter.")