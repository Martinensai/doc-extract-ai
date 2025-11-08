import google.genai as genai
import os
import json
from pathlib import Path

from dotenv import load_dotenv

# --- Configuration ---
load_dotenv()


API_KEY = os.getenv("api_key")

# Configurez votre clé API
genai.configure(api_key=API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. Préparation du Prompt ---

# A. Définir le chemin de votre fichier d'entrée
fichier_txt = Path("data/extracted/decret/2025-652.txt")

# B. Lire le contenu du fichier
try:
    contenu_du_fichier = fichier_txt.read_text(encoding="utf-8")
    print(f"Fichier {fichier_txt} lu avec succès.")
except FileNotFoundError:
    print(f"ERREUR: Le fichier {fichier_txt} n'a pas été trouvé.")
    print("Assurez-vous que la TÂCHE 1 (OCR) a bien été exécutée.")
    exit()

# C. Créer le "schema" JSON que vous voulez que l'IA suive
# (J'ai repris l'exemple de votre toute première question)
json_schema_exemple = """
{
    "numéro_du_décret": "...",
    "date_de_publication": "...",
    "ministère_concerné": "...",
    "objet": "...",
    "articles": {
        "article_1": "...",
        "article_2": "...",
        "article_3": "...",
        "article_4": "...",
        "article_5": "..."
    },
    "signataires": [
        { "nom": "...", "fonction": "..." }
    ]
}
"""

# D. Construire le prompt final (Prompt Engineering)
prompt = f"""
Tu es un expert en analyse de documents administratifs et juridiques.
Ton objectif est d'extraire des métadonnées spécifiques à partir du texte brut
d'un décret qui t'est fourni (ce texte est issu d'un OCR).

Voici le contenu du décret :

--- DÉBUT DU TEXTE ---
{contenu_du_fichier}
--- FIN DU TEXTE ---

Extrais les métadonnées de ce texte et retourne-les au format JSON.
Tu DOIS suivre cet exemple de structure JSON à la lettre :

{json_schema_exemple}

Ne retourne QUE le JSON valide, sans aucun commentaire (ni avant "```json", ni après).
"""

# --- 3. Appel à l'API Gemini ---

print("Envoi de la requête à l'API Gemini (cela peut prendre quelques secondes)...")
try:
    # Configuration pour forcer une réponse JSON (recommandé)
    generation_config = genai.GenerationConfig(
        response_mime_type="application/json"
    )
    
    response = model.generate_content(
        prompt,
        generation_config=generation_config
    )

    # --- 4. Traitement de la Réponse ---
    print("Réponse reçue de l'API :")
    
    # La réponse est une chaîne de caractères (string) qui contient du JSON
    json_string = response.text
    
    # Convertir la chaîne JSON en un dictionnaire Python
    metadata_dict = json.loads(json_string)
    
    # Afficher joliment le dictionnaire
    print(json.dumps(metadata_dict, indent=4, ensure_ascii=False))
    
    # Vous pouvez maintenant sauvegarder ce 'metadata_dict' dans un fichier .json
    output_file = fichier_txt.with_suffix(".json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metadata_dict, f, indent=4, ensure_ascii=False)
    print(f"\n✅ Métadonnées extraites par IA et sauvegardées dans : {output_file}")

except Exception as e:
    print(f"Une erreur est survenue lors de l'appel à l'API : {e}")
    if hasattr(response, 'prompt_feedback'):
        print(f"Feedback du prompt : {response.prompt_feedback}")