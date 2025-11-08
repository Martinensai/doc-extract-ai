import os
import time
import sys

import fitz  # PyMuPDF
from pathlib import Path

import re
import json

import pandas as pd # <-- NOUVELLE DÉPENDANCE





try:
    from PIL import Image
    import pytesseract
    import cv2
    import numpy as np
except ImportError:
    print("Erreur: Des bibliothèques requises sont manquantes.", file=sys.stderr)
    print("Veuillez installer : pip install pymupdf pillow pytesseract opencv-python-headless numpy", file=sys.stderr)
    sys.exit(1)

from pytesseract import Output # <-- NÉCESSAIRE POUR TÂCHE 1

def _private_cv_find_signatures(img_cv, original_img, page_num):
    """
    Utilise OpenCV pour tenter de trouver et découper les signatures
    dans une image donnée.
    """
    extracted_signatures = []
    
    img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, img_thresh = cv2.threshold(img_gray, 180, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(img_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtres heuristiques (à ajuster si nécessaire)
    MIN_AREA = 5000     # Trop petit = bruit
    MAX_AREA = 200000   # Trop grand = lignes, bordures
    PAGE_HEIGHT, PAGE_WIDTH = img_gray.shape
    
    # Zone de recherche : 60% inférieurs de la page
    SIGNATURE_ZONE_TOP_Y = PAGE_HEIGHT * 0.60
    
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)
        
        is_in_signature_zone = y > SIGNATURE_ZONE_TOP_Y
        is_good_size = MIN_AREA < area < MAX_AREA
        
        if is_in_signature_zone and is_good_size:
            padding = 70 # Marge autour de la signature
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(PAGE_WIDTH, x + w + padding)
            y2 = min(PAGE_HEIGHT, y + h + padding)
            
            signature_crop = original_img[y1:y2, x1:x2]
            extracted_signatures.append(signature_crop)
            
    return extracted_signatures

# --- TÂCHE 1 : Fonction d'extraction de texte (OCR) ---

def extract_text_ocr(type_doc: str, numero: str):
    """
    Extrait le texte brut d'un PDF scanné via OCR (Tesseract).
    
    Sortie: data/extracted/{type_doc}/{numero}.txt
    """
    print(f"\n--- TÂCHE 1: Démarrage de l'extraction de texte (OCR) pour {type_doc}/{numero} ---")
    start_time = time.time()
    
    # 1. Définir les chemins
    base_raw_path = Path("data/raw")
    pdf_path = base_raw_path / type_doc / f"{numero}.pdf"
    
    text_output_dir = Path("data/extracted") / type_doc
    text_output_file = text_output_dir / f"{numero}.txt"
    
    if not pdf_path.is_file():
        print(f"Erreur [Texte]: Fichier non trouvé: '{pdf_path}'", file=sys.stderr)
        return False

    text_output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Ouvrir le PDF
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Erreur [Texte]: Impossible d'ouvrir le PDF '{pdf_path}'. {e}", file=sys.stderr)
        return False

    full_text = []
    
    # 3. Traiter chaque page
    for page_num, page in enumerate(doc):
        print(f"  [Texte] Traitement de la page {page_num + 1}/{len(doc)}...")
        
        pix = page.get_pixmap(dpi=300)
        img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        try:
            # L'étape OCR
            text = pytesseract.image_to_string(img_pil, lang='fra')
            full_text.append(f"--- PAGE {page_num + 1} ---")
            full_text.append(text)
        except Exception as e:
            print(f"    Erreur OCR (page {page_num + 1}): {e}", file=sys.stderr)
            full_text.append(f"--- ERREUR OCR PAGE {page_num + 1} ---")

    doc.close()
    
    # 4. Enregistrer le fichier texte
    try:
        text_output_file.write_text("\n\n".join(full_text), encoding="utf-8")
        print(f"  [Texte] Succès. Fichier sauvegardé: {text_output_file}")
    except Exception as e:
        print(f"Erreur [Texte] écriture fichier: {e}", file=sys.stderr)
        return False
    
    print(f"--- TÂCHE 1 Terminée en {time.time() - start_time:.2f} secondes ---")
    return True

# --- TÂCHE 2 : Fonction d'extraction de signatures (CV) ---

def extract_signatures_cv(type_doc: str, numero: str):
    """
    Extrait les signatures potentielles de la **dernière page**
    d'un PDF scanné via Vision par Ordinateur.
    
    Sortie: data/structured/{type_doc}/images/{numero}/...
    """
    print(f"\n--- TÂCHE 2: Démarrage de l'extraction de signatures (CV) pour {type_doc}/{numero} ---")
    start_time = time.time()

    # 1. Définir les chemins
    base_raw_path = Path("data/raw")
    pdf_path = base_raw_path / type_doc / f"{numero}.pdf"
    
    image_output_dir = Path("data/structured") / type_doc / "images" / numero
    
    if not pdf_path.is_file():
        print(f"Erreur [Signatures]: Fichier non trouvé: '{pdf_path}'", file=sys.stderr)
        return False

    image_output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Ouvrir le PDF
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Erreur [Signatures]: Impossible d'ouvrir le PDF '{pdf_path}'. {e}", file=sys.stderr)
        return False

    total_images_found = 0
    
    # 3. Traiter uniquement la dernière page
    if len(doc) == 0:
        print(f"  [Signatures] Erreur: Le document '{pdf_path.name}' est vide.")
        doc.close()
        return False
        
    # Accéder directement à la dernière page (index -1)
    page_num = len(doc) - 1
    page = doc[-1] 
    
    print(f"  [Signatures] Analyse de la dernière page (Page {page_num + 1}/{len(doc)})...")

    # Rendu de la page en image (haute résolution)
    pix = page.get_pixmap(dpi=300)
    img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # Conversion en format OpenCV
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    
    # Appel de la fonction d'aide privée
    signatures = _private_cv_find_signatures(img_cv, img_cv, page_num)
    
    if signatures:
        print(f"    -> {len(signatures)} signature(s) potentielle(s) trouvée(s).")
        # 4. Enregistrer les images découpées
        for i, sig_crop in enumerate(signatures):
            # Nom de fichier incluant le numéro de page (utile)
            img_name = f"page_{page_num + 1}_signature_{i + 1}.png"
            img_save_path = str(image_output_dir / img_name)
            
            try:
                cv2.imwrite(img_save_path, sig_crop)
                total_images_found += 1
            except Exception as e:
                print(f"      Erreur sauvegarde image: {e}", file=sys.stderr)

    doc.close()
    
    if total_images_found == 0:
        print("    -> Aucune signature détectée selon les filtres actuels.")
        
    print(f"  [Signatures] Succès. {total_images_found} image(s) sauvegardée(s) dans: {image_output_dir}")
    print(f"--- TÂCHE 2 Terminée en {time.time() - start_time:.2f} secondes ---")
    return True

def clean_text(text):
    if not text: return ""
    text = re.sub(r'--- PAGE \d+ ---', ' ', text)
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def convert_article_key(article_num_str):
    article_num_str = article_num_str.lower().strip()
    if article_num_str == 'premier': return 'article_1'
    if article_num_str.isdigit(): return f'article_{article_num_str}'
    return article_num_str

def clean_signatory_name(name):
    name = re.sub(r'[!/]', '', name)
    name = re.sub(r'^\.*', '', name)
    if 'Patrice' in name and 'TAL' in name: return 'Patrice TALON'
    if 'omuald' in name and 'WADAGN' in name: return 'Romuald WADAGNI'
    if 'José' in name or 'TONATO' in name: return 'José TONATO'
    return name.strip()

def clean_signatory_function(func):
    func = re.sub(r'\s*\|\s*', '', func)
    return clean_text(func)


# =====================================================================
# --- SECTION 2 : LOGIQUE D'EXTRACTION (TÂCHE 3) ---
# (Inchangé - C'est la fonction qui lit le .txt)
# =====================================================================

def extract_metadata_decret(text, type_doc):
    """
    Contient la logique d'extraction (regex) pour un décret.
    (INCHANGÉ)
    """
    metadata = {
        "type_doc": type_doc, "numéro_du_décret": None,
        "date_de_publication": None, "ministère_concerné": None,
        "objet": None, "articles": {}, "signataires": []
    }
    
    text_linear = re.sub(r'--- PAGE \d+ ---', ' ', text)

    # 1. Numéro
    match = re.search(r'DÉCRET N° ([\d\s—-]+)', text_linear)
    if match: metadata['numéro_du_décret'] = match.group(1).strip()

    # 2. Date
    match = re.search(r'Fait à Cotonou, le ([\d\s\w]+)', text_linear, re.IGNORECASE)
    if match: metadata['date_de_publication'] = match.group(1).strip()

    # 3. Objet
    match = re.search(r'DU \d{4}\s*(portant[\s\S]+?)\s*LE PRÉSIDENT', text_linear, re.DOTALL)
    if match: metadata['objet'] = clean_text(match.group(1))

    # 4. Ministère
    match = re.search(r'sur proposition du (Ministre[\s\S]+?),', text_linear)
    if match: metadata['ministère_concerné'] = clean_text(match.group(1))

    # 5. Articles
    articles_block_match = re.search(r'DÉCRÈTE([\s\S]+?)Fait à Cotonou', text_linear, re.DOTALL)
    if articles_block_match:
        articles_block = articles_block_match.group(1)
        article_matches = re.findall(
            r"(Article (?:premier|\d+))([\s\S]+?)(?=\s*Article (?:premier|\d+)|\s*Fait à Cotonou)",
            articles_block
        )
        for match in article_matches:
            key = convert_article_key(match[0].replace('Article ', '').strip())
            value = clean_text(match[1])
            metadata['articles'][key] = value

    # 6. Signataires
    # Cette regex est bien meilleure car le texte est propre
    sig_block_match = re.search(r'Fait à Cotonou.*?\n([\s\S]+?)AMPLIATIONS', text, re.DOTALL)
    if sig_block_match:
        sig_block = sig_block_match.group(1)
        # On cherche des blocs Fonction + Nom
        signatory_matches = re.findall(
            r'((?:Par le|Le Ministre)[\s\S]+?)\n\s*([A-Z\s]{5,})',
            sig_block
        )
        for match in signatory_matches:
            fonction = clean_signatory_function(match[0])
            nom = clean_signatory_name(match[1])
            if "Patrice" in nom or "Romuald" in nom or "José" in nom:
                 metadata['signataires'].append({"nom": nom, "fonction": fonction})

    return metadata


# =====================================================================
# --- SECTION 3 : FONCTIONS DE PIPELINE (TÂCHES 1, 2, 3) ---
# =====================================================================

# --- TÂCHE 1 (AMÉLIORÉE) : OCR CONSCIENT DE LA MISE EN PAGE ---

def extract_layout_aware_text_ocr(type_doc: str, numero: str):
    """
    TÂCHE 1 (AMÉLIORÉE)
    Extrait le texte brut d'un PDF scanné en utilisant l'analyse
    de mise en page de Tesseract pour "linéariser" le texte
    correctement, en respectant les colonnes.
    
    Sortie: data/extracted/{type_doc}/{numero}.txt
    """
    print(f"\n--- TÂCHE 1 (Améliorée): Démarrage de l'OCR (Layout-Aware) pour {type_doc}/{numero} ---")
    start_time = time.time()
    
    base_raw_path = Path("data/raw")
    pdf_path = base_raw_path / type_doc / f"{numero}.pdf"
    
    text_output_dir = Path("data/extracted") / type_doc
    text_output_file = text_output_dir / f"{numero}.txt"
    
    if not pdf_path.is_file():
        print(f"Erreur [Texte]: Fichier non trouvé: '{pdf_path}'", file=sys.stderr)
        return False

    text_output_dir.mkdir(parents=True, exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Erreur [Texte]: Impossible d'ouvrir le PDF '{pdf_path}'. {e}", file=sys.stderr)
        return False

    full_text_pages = []
    
    for page_num, page in enumerate(doc):
        print(f"  [Texte] Traitement de la page {page_num + 1}/{len(doc)}...")
        
        pix = page.get_pixmap(dpi=300)
        img_pil = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        try:
            # ICI LE CHANGEMENT : on utilise image_to_data
            # On récupère un DataFrame pandas avec les coordonnées
            ocr_data = pytesseract.image_to_data(img_pil, lang='fra', output_type=Output.DATAFRAME)
            
            # Filtrer les mots vides ou à faible confiance
            ocr_data = ocr_data[ocr_data.conf > 0]
            ocr_data = ocr_data.dropna(subset=['text'])
            ocr_data['text'] = ocr_data['text'].str.strip()
            ocr_data = ocr_data[ocr_data.text != '']

            # Tesseract fournit des numéros de bloc, paragraphe et ligne.
            # Nous pouvons les utiliser pour regrouper le texte.
            
            page_text = []
            # Grouper par bloc, puis paragraphe, puis ligne
            grouped_lines = ocr_data.groupby(['block_num', 'par_num', 'line_num'])
            
            for _, line_df in grouped_lines:
                # Trier les mots de la ligne par leur position 'left' (x)
                line_df = line_df.sort_values(by='left')
                # Joindre les mots pour former la ligne
                line_text = ' '.join(line_df['text'])
                page_text.append(line_text)

            full_text_pages.append(f"--- PAGE {page_num + 1} ---")
            # Joindre les lignes avec des sauts de ligne
            full_text_pages.append("\n".join(page_text))

        except Exception as e:
            print(f"    Erreur OCR (page {page_num + 1}): {e}", file=sys.stderr)
            full_text_pages.append(f"--- ERREUR OCR PAGE {page_num + 1} ---")

    doc.close()
    
    # 4. Enregistrer le fichier texte
    try:
        text_output_file.write_text("\n\n".join(full_text_pages), encoding="utf-8")
        print(f"  [Texte] Succès. Fichier (layout-aware) sauvegardé: {text_output_file}")
    except Exception as e:
        print(f"Erreur [Texte] écriture fichier: {e}", file=sys.stderr)
        return False
    
    print(f"--- TÂCHE 1 (Améliorée) Terminée en {time.time() - start_time:.2f} secondes ---")
    return True


# --- TÂCHE 3 : Fonction d'extraction des Métadonnées (JSON) ---

# =====================================================================
# --- TÂCHE 3 : Fonction d'extraction des Métadonnées (JSON) ---
# (VERSION CORRIGÉE)
# =====================================================================

def extract_metadata_json(type_doc: str, numero: str):
    """
    TÂCHE 3 (Corrigée)
    Extrait les métadonnées (JSON) depuis un fichier texte brut (post-OCR).
    Dépend de la TÂCHE 1.
    """
    print(f"\n--- TÂCHE 3: Démarrage de l'extraction des Métadonnées (JSON) pour {type_doc}/{numero} ---")
    start_time = time.time()
    
    base_extracted_path = Path("data/extracted")
    
    # 1. Définir le chemin d'ENTRÉE (.txt)
    text_input_file = base_extracted_path / type_doc / f"{numero}.txt"
    
    # 2. Définir le dossier de SORTIE... (CORRECTION ICI)
    json_output_dir = base_extracted_path / type_doc
    
    # 3. ...PUIS définir le fichier de SORTIE (.json) (CORRECTION ICI)
    json_output_file = json_output_dir / f"{numero}.json"
    
    # Le reste de la fonction est identique
    
    if not text_input_file.is_file():
        print(f"Erreur [JSON]: Fichier texte non trouvé: '{text_input_file}'", file=sys.stderr)
        return False
        
    json_output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        print(f"  [JSON] Lecture de {text_input_file}...")
        text_content = text_input_file.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Erreur [JSON]: Impossible de lire le fichier '{text_input_file}'. {e}", file=sys.stderr)
        return False
        
    print(f"  [JSON] Analyse des métadonnées (Type: {type_doc})...")
    metadata = {}
    
    if type_doc == "decret":
        metadata = extract_metadata_decret(text_content, type_doc)
    elif type_doc == "loi":
        print(f"    Erreur [JSON]: Logique d'extraction pour '{type_doc}' non implémentée.", file=sys.stderr)
        return False
    else:
        print(f"    Erreur [JSON]: Type de document '{type_doc}' non supporté.", file=sys.stderr)
        return False
        
    try:
        with open(json_output_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)
        print(f"  [JSON] Succès. Fichier sauvegardé: {json_output_file}")
    except Exception as e:
        print(f"Erreur [JSON] écriture fichier: {e}", file=sys.stderr)
        return False

    print(f"--- TÂCHE 3 Terminée en {time.time() - start_time:.2f} secondes ---")
    return True
# --- Point d'entrée principal (Exemple d'utilisation) ---

if __name__ == "__main__":

    # --- Configuration ---
    TYPE_DOC_TEST = "decret"
    NUMERO_TEST = "2025-652" # Sans l'extension .pdf
    
    # --- Créer un faux fichier PDF pour le test ---
    print("--- MISE EN PLACE DU TEST ---")
    (Path("data/raw") / TYPE_DOC_TEST).mkdir(parents=True, exist_ok=True)
    pdf_test_path = Path("data/raw") / TYPE_DOC_TEST / f"{NUMERO_TEST}.pdf"
    
    # Placez votre vrai PDF 2025-652.pdf à cet emplacement
    # pour que le test fonctionne.
    if not pdf_test_path.is_file():
        print(f"!! ATTENTION: Le fichier PDF '{pdf_test_path}' n'a pas été trouvé.")
        print("  Veuillez placer votre fichier PDF de test à cet emplacement.")
        # On crée un PDF vide pour éviter que le script ne plante
        try:
            doc = fitz.open()
            doc.new_page()
            doc.save(pdf_test_path)
            doc.close()
            print(f"  Un PDF de test VIDE a été créé. L'OCR ne trouvera rien.")
        except Exception as e:
            print(f"  Impossible de créer un PDF de test. {e}")
            sys.exit(1) # Arrêter le script si on ne peut pas continuer
    else:
        print(f"Fichier PDF de test trouvé : {pdf_test_path}")

    print("---------------------------------")
    
    
    # --- Lancement du Pipeline ---
    print(f"Lancement du pipeline pour {TYPE_DOC_TEST}/{NUMERO_TEST}...")

    # TÂCHE 1 (Améliorée) : PDF -> TXT (Layout-Aware)
    success_t1 = False
    try:
        success_t1 = extract_layout_aware_text_ocr(TYPE_DOC_TEST, NUMERO_TEST)
    except pytesseract.pytesseract.TesseractNotFoundError:
        print("ERREUR FATALE: Tesseract n'est pas installé ou n'est pas dans le PATH.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERREUR FATALE TÂCHE 1: {e}", file=sys.stderr)

"""
    # TÂCHE 2 : PDF -> Images (Signatures)
    success_t2 = False
    try:
        success_t2 = extract_signatures_cv(TYPE_DOC_TEST, NUMERO_TEST)
    except Exception as e:
        print(f"ERREUR FATALE TÂCHE 2: {e}", file=sys.stderr)

    # TÂCHE 3 : TXT -> JSON
    success_t3 = False
    if success_t1: # Ne peut s'exécuter que si la Tâche 1 a réussi
        try:
            success_t3 = extract_metadata_json(TYPE_DOC_TEST, NUMERO_TEST)
        except Exception as e:
            print(f"ERREUR FATALE TÂCHE 3: {e}", file=sys.stderr)
    else:
        print("\nSkipping TÂCHE 3 car la TÂCHE 1 a échoué.")

    print("\n--- Pipeline Terminé ---")
    print(f"Tâche 1 (Texte Layout-Aware): {'Succès' if success_t1 else 'Échec'}")
    print(f"Tâche 2 (Signatures): {'Succès' if success_t2 else 'Échec'}")
    print(f"Tâche 3 (JSON): {'Succès' if success_t3 else 'Échec'}")

    # Exemple de test avec votre document
    type_doc_exemple = "decret"
    numero_exemple = "2024-1051"
    
    print("="*50)
    print("DÉBUT DU TRAITEMENT MODULAIRE")
    print("="*50)
     # --- -----------------------
    
    
    print("\n" + "="*50)
    print("TRAITEMENT TERMINÉ")
    print("="*50)

    # Vérification si Tesseract est accessible
    try:
        tess_version = pytesseract.get_tesseract_version()
        print(f"Tesseract version {tess_version} détecté. Prêt à démarrer.")
    except pytesseract.TesseractNotFoundError:
        print("ERREUR: Tesseract n'est pas trouvé.", file=sys.stderr)
        print("Veuillez l'installer et/ou l'ajouter à votre PATH système.", file=sys.stderr)
        sys.exit(1)

    # Appel de la Tâche 1 (Texte)
    success_text = extract_text_ocr(type_doc_exemple, numero_exemple)
    if not success_text:
        print("Échec de l'extraction de texte.")

    # Appel de la Tâche 2 (Signatures)
    success_signatures = extract_signatures_cv(type_doc_exemple, numero_exemple)
    if not success_signatures:
        print("Échec de l'extraction de signatures.")
    """