import os
import google.generativeai as genai
from dotenv import load_dotenv

# --- Configuration de l'API ---
try:
    load_dotenv()
    API_KEY = os.getenv("GEMINI_API_KEY")
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY non trouvée dans le fichier .env")
    genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"Erreur lors de la configuration de Gemini: {e}")
    # Cette erreur sera visible dans la console qui lance Streamlit

# --- Prompt Système (Tiré de votre fichier prompts.py) ---
DOCUMENT_SYSTEM_PROMPT = """Tu es un assistant expert en droit béninois, spécialisé dans l'analyse de documents officiels.
Ton rôle est de répondre aux questions de l'utilisateur UNIQUEMENT sur la base du document fourni.
Fournis des réponses courtes, précises et cite tes sources (ex: "Selon l'Article 2...", "L'objet du décret est...").
Si la réponse ne se trouve pas dans le texte, réponds poliment que l'information n'est pas disponible dans ce document.
"""

# Initialiser le modèle une seule fois
try:
    # Utilisons le modèle flash pour des réponses rapides
    # --- CORRECTION ---
    # Le system_instruction est passé ici, lors de l'initialisation
    model = genai.GenerativeModel(
        'gemini-2.5-flash-preview-09-2025',
        system_instruction=DOCUMENT_SYSTEM_PROMPT
    )
except Exception as e:
    model = None
    print(f"Erreur lors de l'initialisation du modèle Gemini: {e}")


def get_gemini_response(context: str, chat_history: list, user_question: str) -> str:
    """
    Génère une réponse de chatbot en utilisant Gemini, basée sur un contexte et un historique.
    """
    if model is None:
        return "Erreur: Le modèle Gemini n'a pas pu être initialisé. Vérifiez votre clé API et la console."

    # Formater l'historique pour l'API Gemini
    # L'historique de Streamlit contient des objets, nous devons les convertir
    formatted_history = []
    for message in chat_history:
        role = "user" if message["role"] == "user" else "model"
        formatted_history.append({"role": role, "parts": [message["content"]]})

    # Construction du message complet pour le LLM
    # Nous donnons le contexte complet à chaque fois
    prompt_parts = [
        f"CONTEXTE DOCUMENT:\n---\n{context}\n---\n",
        f"QUESTION: {user_question}"
    ]
    
    try:
        # --- CORRECTION ---
        # On ne passe plus system_instruction ici
        chat_session = model.start_chat(
            history=formatted_history
        )
        
        # Envoyer le nouveau message (contexte + question)
        response = chat_session.send_message(" ".join(prompt_parts))
        
        return response.text

    except Exception as e:
        print(f"Erreur lors de l'appel à l'API Gemini: {e}")
        return f"Désolé, une erreur est survenue lors de la connexion à l'IA : {e}"