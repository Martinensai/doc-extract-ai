"""app.py
Streamlit app: minimal chatbot UI that queries a retriever.
Run with: streamlit run src/chatbot/app.py
"""
import streamlit as st
from src.chatbot.retriever import retrieve_answer

st.set_page_config(page_title="DocuExtract Benin", layout="centered")

st.title("DocuExtract Benin — Chatbot")
query = st.text_input("Posez une question sur les décrets / arrêtés:")

if query:
    with st.spinner("Recherche..."):
        ans = retrieve_answer(query)
    st.markdown("**Réponse**")
    st.write(ans)
