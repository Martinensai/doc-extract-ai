import os
import requests
from typing import Literal

DocumentType = Literal["decret", "loi", "ordonnance", "arrete", "accords", "decision"]

def telecharger_document_benin(numero: str, type_doc: DocumentType) -> str:
    """
    Télécharge un document public béninois et le stocke dans data/raw/<type_doc>/<numero>.pdf.

    Args:
        numero (int): Le numéro du document (utilisé dans le nom du fichier).
        type_doc (DocumentType): Le type de document ('decrets', 'loi', etc.).
                                 Doit correspondre à l'un des types valides.

    Returns:
        str: Le chemin d'accès au fichier téléchargé ou une chaîne vide en cas d'échec.
    """
    
    BASE_URL = "https://sgg.gouv.bj/doc/"
    url_telechargement = f"{BASE_URL}{type_doc}-{numero}/download"
    
    base_dir = "data/raw"
    dossier_destination = os.path.join(base_dir, type_doc)
    nom_fichier = f"{numero}.pdf"
    chemin_complet = os.path.join(dossier_destination, nom_fichier)

    try:
        os.makedirs(dossier_destination, exist_ok=True)
        print(f"Dossier de destination vérifié/créé : {dossier_destination}")
    except OSError as e:
        print(f"Erreur lors de la création du dossier : {e}")
        return ""

    print(f"Tentative de téléchargement depuis : {url_telechargement}")
    
    try:
        response = requests.get(url_telechargement, stream=True, timeout=30)
        
        if response.status_code == 200:
            with open(chemin_complet, 'wb') as fichier:
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

if __name__ == "__main__":
    chemin_decret = telecharger_document_benin(numero='2024-1051', type_doc="decret")
    print("-" * 30)