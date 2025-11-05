import os
import time
import sys

import fitz  # PyMuPDF
from pathlib import Path




try:
    from PIL import Image
    import pytesseract
    import cv2
    import numpy as np
except ImportError:
    print("Erreur: Des bibliothèques requises sont manquantes.", file=sys.stderr)
    print("Veuillez installer : pip install pymupdf pillow pytesseract opencv-python-headless numpy", file=sys.stderr)
    sys.exit(1)

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


# --- Point d'entrée principal (Exemple d'utilisation) ---

if __name__ == "__main__":
    # Exemple de test avec votre document
    type_doc_exemple = "decret"
    numero_exemple = "2024-1051"
    
    print("="*50)
    print("DÉBUT DU TRAITEMENT MODULAIRE")
    print("="*50)
     # --- Méthode 1 (Recommandée) ---
    extract_tables_img2table(type_doc_exemple, numero_exemple)
    


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
    
   