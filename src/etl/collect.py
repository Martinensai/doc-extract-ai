import os
import requests
from typing import Literal

# Définition des types de documents valides pour une meilleure robustesse
DocumentType = Literal["decret", "loi", "ordonnance", "arrete", "accords", "decision"]

def telecharger_document_benin(numero: str, type_doc: DocumentType) -> str:
    """
    Télécharge un document public béninois et le stocke dans data/raw/<type_doc>/<numero>.pdf.

    Args:
        numero (int): Le numéro du document (utilisé dans le nom du fichier).
        type_doc (DocumentType): Le type de document ('decrets', 'loi', etc.).
                                 Doit correspondre à l'un des types valides.

    Returns:
        str: Le chemin d'accès au fichier téléchargé.
    """
    # 1. Construction de l'URL
    BASE_URL = "https://sgg.gouv.bj/doc/"
    # L'URL finale est BASE_URL + type_doc + '/' + numero + '.pdf'
    # Ex: https://sgg.gouv.bj/doc/decrets/123.pdf
    url_telechargement = f"{BASE_URL}{type_doc}-{numero}/download"
    
    # 2. Définition du chemin de destination
    # Chemin racine : data/raw/
    base_dir = "data/raw"
    # Chemin du sous-dossier : data/raw/<type_doc>/
    dossier_destination = os.path.join(base_dir, type_doc)
    # Nom du fichier : <numero>.pdf
    nom_fichier = f"{numero}.pdf"
    # Chemin complet : data/raw/<type_doc>/<numero>.pdf
    chemin_complet = os.path.join(dossier_destination, nom_fichier)

    # 3. Création du dossier s'il n'existe pas
    try:
        # L'option 'exist_ok=True' évite une erreur si le dossier existe déjà
        os.makedirs(dossier_destination, exist_ok=True)
        print(f"Dossier de destination vérifié/créé : {dossier_destination}")
    except OSError as e:
        print(f"Erreur lors de la création du dossier : {e}")
        return ""

    # 4. Téléchargement du fichier
    print(f"Tentative de téléchargement depuis : {url_telechargement}")
    
    try:
        # Utilisation de 'stream=True' pour les gros fichiers
        response = requests.get(url_telechargement, stream=True, timeout=30)
        
        # Vérification du statut de la réponse HTTP (200 OK)
        if response.status_code == 200:
            with open(chemin_complet, 'wb') as fichier:
                # Écriture du contenu par blocs
                for chunk in response.iter_content(chunk_size=8192):
                    fichier.write(chunk)
            
            print(f"✅ Document téléchargé avec succès : {chemin_complet}")
            return chemin_complet
        else:
            print(f"❌ Erreur de téléchargement : Statut HTTP {response.status_code} pour l'URL {url_telechargement}")
            return ""

    except requests.exceptions.RequestException as e:
        print(f"❌ Une erreur s'est produite lors de la requête : {e}")
        return ""

# --- Exemple d'utilisation ---
if __name__ == "__main__":
        # 1. Télécharger un décret (ex: décret numéro 123)
    chemin_decret = telecharger_document_benin(numero='2024-1051', type_doc="decret")
    print("-" * 30)


