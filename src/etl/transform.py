"""
Ce script gère l'étape de **Transformation (T)** du pipeline ETL.

Son rôle principal est de prendre un fichier texte brut (généré par l'OCR)
et d'utiliser l'API Google Gemini (gemini-2.5-flash) pour en extraire
les informations structurées.

Il lit le .txt, envoie une requête à l'IA avec un schéma JSON attendu,
et sauvegarde la réponse de l'IA dans un fichier .json.

Fonction principale :
- transform_text_to_json
"""

import google.generativeai as genai
import os
import json
import time
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("Erreur: Clé API 'GEMINI_API_KEY' non trouvée dans .env", file=sys.stderr)
    
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"Erreur lors de la configuration de genai: {e}", file=sys.stderr)

try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Erreur lors de la création du modèle Gemini: {e}", file=sys.stderr)
    model = None

JSON_SCHEMA_DECRET = """
{
  "numéro_du_décret": "...",
  "date_de_publication": "...",
  "ministère_concerné": "...",
  "objet": "...",
  "articles": [
    {
      "numero": "Numéro de l'article (ex: Article 1, Article 2, Article 3-bis)",
      "texte": "Contenu textuel complet de cet article spécifique."
    }
  ],
  "signataires": [
      { "nom": "...", "fonction": "..." }
  ]
}
"""

def transform_text_to_json(type_doc: str, numero: str):
    """
    Extrait les métadonnées d'un fichier texte (via l'IA Gemini)
    et les sauvegarde en JSON.

    Entrée: data/extracted/{type_doc}/{numero}.txt
    Sortie: data/extracted/{type_doc}/{numero}.json
    """
    print(f"\n--- TÂCHE 2: Démarrage de la transformation JSON (IA) pour {type_doc}/{numero} ---")
    start_time = time.time()

    if model is None:
        print("Erreur [JSON]: Le modèle Gemini n'a pas été initialisé.", file=sys.stderr)
        return False

    base_extracted_path = Path("data/extracted")
    input_txt_path = base_extracted_path / type_doc / f"{numero}.txt"
    output_json_path = input_txt_path.with_suffix(".json")

    try:
        contenu_du_fichier = input_txt_path.read_text(encoding="utf-8")
        print(f"  [JSON] Fichier texte lu: {input_txt_path}")
    except FileNotFoundError:
        print(f"Erreur [JSON]: Fichier .txt non trouvé: '{input_txt_path}'", file=sys.stderr)
        print("  Assurez-vous que la TÂCHE 1 (OCR) a bien été exécutée.", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Erreur [JSON] lors de la lecture du fichier: {e}", file=sys.stderr)
        return False
        
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

    {JSON_SCHEMA_DECRET}

    Ne retourne QUE le JSON valide, sans aucun commentaire (ni avant "```json", ni après).
    """

    print("  [JSON] Envoi de la requête à l'API Gemini...")
    try:
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json"
        )
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        json_string = response.text
        metadata_dict = json.loads(json_string)
        
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=4, ensure_ascii=False)
            
        print(f"  [JSON] Succès. Fichier sauvegardé: {output_json_path}")

    except Exception as e:
        print(f"Erreur [JSON] (API ou sauvegarde): {e}", file=sys.stderr)
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            print(f"  Feedback du prompt : {response.prompt_feedback}", file=sys.stderr)
        return False

    print(f"--- TÂCHE 2 Terminée en {time.time() - start_time:.2f} secondes ---")
    return True

if __name__ == "__main__":
    print("Test de la fonction transform_text_to_json...")
    
    TYPE_TEST = "decret"
    NUMERO_TEST = "2025-652"
    
    if transform_text_to_json(type_doc=TYPE_TEST, numero=NUMERO_TEST):
         print(f"Test réussi pour {TYPE_TEST}/{NUMERO_TEST}.")
    else:
         print(f"Test échoué pour {TYPE_TEST}/{NUMERO_TEST}.")