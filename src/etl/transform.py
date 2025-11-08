
import google.generativeai as genai
import os
import json
import time  # Ajouté pour le timing
import sys   # Ajouté pour stderr
from pathlib import Path
from dotenv import load_dotenv

# --- Configuration (A exécuter une seule fois au chargement du module) ---
load_dotenv()
API_KEY = os.getenv("api_key")

# Vérification de la clé API
if not API_KEY:
    print("Erreur: Clé API 'GEMINI_API_KEY' non trouvée dans .env", file=sys.stderr)
    # Vous pourriez vouloir arrêter le script ici avec sys.exit(1)
    # ou laisser la fonction échouer si elle est appelée.
    
# Configurez votre clé API
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"Erreur lors de la configuration de genai: {e}", file=sys.stderr)

# Initialiser le modèle une seule fois
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    print(f"Erreur lors de la création du modèle Gemini: {e}", file=sys.stderr)
    model = None # Gérer cet état dans la fonction

# --- Schéma JSON (défini comme constante) ---
# (J'ai repris l'exemple de votre toute première question)
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

    # 1. Définir les chemins (logique identique à extract_text_ocr)
    base_extracted_path = Path("data/extracted")
    input_txt_path = base_extracted_path / type_doc / f"{numero}.txt"
    
    # Le fichier de sortie aura le même nom, mais avec l'extension .json
    output_json_path = input_txt_path.with_suffix(".json")

    # 2. Lire le fichier texte (sortie de l'OCR)
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
        
    # 3. Construire le prompt
    # (Utilise la constante JSON_SCHEMA_DECRET définie ci-dessus)
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

    # 4. Appel à l'API Gemini et sauvegarde
    print("  [JSON] Envoi de la requête à l'API Gemini...")
    try:
        # Configuration pour forcer une réponse JSON
        generation_config = genai.GenerationConfig(
            response_mime_type="application/json"
        )
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )

        # La réponse est une chaîne de caractères (string) qui contient du JSON
        json_string = response.text
        
        # Convertir la chaîne JSON en un dictionnaire Python (valide le format)
        metadata_dict = json.loads(json_string)
        
        # Sauvegarder le JSON (ré-encodé pour un joli format)
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=4, ensure_ascii=False)
            
        print(f"  [JSON] Succès. Fichier sauvegardé: {output_json_path}")

    except Exception as e:
        print(f"Erreur [JSON] (API ou sauvegarde): {e}", file=sys.stderr)
        # Tenter d'afficher des diagnostics supplémentaires si disponibles
        if 'response' in locals() and hasattr(response, 'prompt_feedback'):
            print(f"  Feedback du prompt : {response.prompt_feedback}", file=sys.stderr)
        return False

    print(f"--- TÂCHE 2 Terminée en {time.time() - start_time:.2f} secondes ---")
    return True

# --- Exemple d'utilisation (pour tester) ---
if __name__ == "__main__":
    print("Test de la fonction transform_text_to_json...")
    
    # Assurez-vous qu'un fichier .txt existe à cet emplacement pour le test
    # (par exemple, 'data/extracted/decret/2025-652.txt')
    TYPE_TEST = "decret"
    NUMERO_TEST = "2025-652"
    
    if transform_text_to_json(type_doc=TYPE_TEST, numero=NUMERO_TEST):
         print(f"Test réussi pour {TYPE_TEST}/{NUMERO_TEST}.")
    else:
         print(f"Test échoué pour {TYPE_TEST}/{NUMERO_TEST}.")