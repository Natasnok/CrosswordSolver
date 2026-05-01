from sys import platform
import cv2
import pytesseract
import numpy as np
import re
from difflib import SequenceMatcher


if platform == "win32":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

_SECTION_H = re.compile(r'H\s*O\s*R\s*I\s*Z\s*O\s*N\s*T\s*A\s*L\s*E\s*M\s*E\s*N\s*T', re.I)
_SECTION_V = re.compile(r'V\s*E\s*R\s*T\s*I\s*C\s*A\s*L\s*E\s*M\s*E\s*N\s*T', re.I)


def _deskew(gray):
    coords = np.column_stack(np.where(gray < 128))
    if len(coords) < 50:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    if abs(angle) < 0.3:
        return gray
    h, w = gray.shape
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(
        gray, M, (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )


def preprocess_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.fastNlMeansDenoising(gray, h=10)
    gray = _deskew(gray)
    gray = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31, 10
    )
    return gray


def _find_section_cut(img):
    gray = preprocess_image(img)
    data = pytesseract.image_to_data(
        gray,
        lang="fra",
        config="--oem 3 --psm 6",
        output_type=pytesseract.Output.DICT
    )
    scale = gray.shape[0] / img.shape[0]

    for i, text in enumerate(data["text"]):
        if _SECTION_V.search(str(text)):
            cut_preprocessed = max(0, data["top"][i] - 20)
            return int(cut_preprocessed / scale)
    return None


def _ocr_zone(img_zone, psm=4):
    gray = preprocess_image(img_zone)
    return pytesseract.image_to_string(
        gray,
        lang="fra",
        config=f"--oem 3 --psm {psm}"
    )


def ocr_image(img):
    cut_y = _find_section_cut(img)

    if cut_y and img.shape[0] // 4 < cut_y < img.shape[0] * 3 // 4:
        text_h = _ocr_zone(img[:cut_y], psm=4)
        text_v = _ocr_zone(img[cut_y:], psm=4)
        return text_h, text_v

    text_full = _ocr_zone(img, psm=6)
    parts_v = _SECTION_V.split(text_full, maxsplit=1)
    if len(parts_v) == 2:
        parts_h = _SECTION_H.split(parts_v[0], maxsplit=1)
        return parts_h[-1], parts_v[1]

    return "", text_full


def clean_mot(mot):
    mot = re.sub(r'\b(?:HORIZONTALEMENT|VERTICALEMENT)\b', '', mot)
    mot = mot.strip(' ,.;:-\u2013\u2014_|\n\r\t')
    return re.sub(r'\s{2,}', ' ', mot).strip()

def is_valid(mot):
    return len(mot) >= 2 and bool(re.search(r'[A-Za-zÀ-ÿ]', mot))


def extract_definitions(text):
    text = clean_mot(text)
    text = re.sub(r'\b([IVXLCDM]+|\d+)\.\s*', '', text)
    return [d.strip() for d in text.split('.') if d.strip()]


def scan_definitions(nom_image):
    img = cv2.imread(nom_image)
    if img is None:
        raise ValueError(f"Image introuvable : {nom_image}")

    text_h, text_v = ocr_image(img)

    result = []
    print("Texte horizontal extrait :", text_h)
    print("Texte vertical extrait :", text_v)

    # Découper en définitions
    defs_h = extract_definitions(text_h)
    for defi in defs_h:
        result.append({'mot': defi, 'direction': 'H'})
    
    # Vertical  
    defs_v = extract_definitions(text_v)
    for defi in defs_v:
        result.append({'mot': defi, 'direction': 'V'})
    
    return result