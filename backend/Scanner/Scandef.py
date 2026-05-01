from sys import platform
import cv2
import pytesseract
import numpy as np
import re
from difflib import SequenceMatcher

if platform == "win32":
    pytesseract.pytesseract.tesseract_cmd = r"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

PREP = re.compile(
    r'\b(?:de|des|du|le|la|les|à|a|au|aux|en|par|sur|un|une|et|ou|'
    r'se|ce|ne|y|qu|dont|Nations|Saint|Sainte|Mont|Col|Lac|son|sa|ses|'
    r'leur|leurs|cette|cet|il|elle|ils|elles|qui|que|où|mais|car|'
    r'si|ni|or|pour|avec|sans|sous|vers|entre|depuis|après|avant|chez|'
    r'très|bien|plus|moins|tout|tous|toute|toutes|même|autre|autres)$',
    re.IGNORECASE
)

_NUM_LEAD = re.compile(r'^\s*(?:[IVXLCDM]{1,6}|\d{1,3})\s*\.\s*')
_NUM_MID = re.compile(r'\s+(?:[IVXLCDM]{2,6}|\d+)\s*[.,]?\s*(?=[A-Za-zÀ-ÿ\s]|$)')
_ARTIFACT = re.compile(r'(?<!\w)\b[A-Za-zÀ-ÿ]{1,2}\.(?=\s+[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ0-9])')
_SECTION_H = re.compile(r'H\s*O\s*R\s*I\s*Z\s*O\s*N\s*T\s*A\s*L\s*E\s*M\s*E\s*N\s*T', re.I)
_SECTION_V = re.compile(r'V\s*E\s*R\s*T\s*I\s*C\s*A\s*L\s*E\s*M\s*E\s*N\s*T', re.I)
_CAP_WORD = re.compile(r'^[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ][a-zàâäçéèêëîïôöùûüÿ]')

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
    return cv2.warpAffine(gray, M, (w, h),
                          flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_REPLICATE)

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
        gray, lang="fra",
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
        gray, lang="fra",
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

def normalize_text(text):
    text = text.replace('\u2019', "'").replace('\u2018', "'")
    text = text.replace('\n', ' ')
    return re.sub(r'\s+', ' ', text).strip()

def _clean_section_text(text):
    text = _SECTION_H.sub(' ', text)
    text = _SECTION_V.sub(' ', text)
    text = _NUM_LEAD.sub(' ', text)
    text = _NUM_MID.sub(' ', text)
    text = _ARTIFACT.sub(' ', text)
    return re.sub(r'\s{2,}', ' ', text).strip()

def clean_mot(mot):
    mot = mot.strip(' ,.;:-\u2013\u2014_')
    return re.sub(r'\s{2,}', ' ', mot).strip()

def is_valid(mot):
    return len(mot) >= 3 and bool(re.search(r'[A-Za-zÀ-ÿ]', mot))

def split_on_capitals(mot):
    parts = mot.split()
    result, current = [], []

    for i, word in enumerate(parts):
        current.append(word)
        if i < len(parts) - 1:
            next_word = parts[i + 1]
            next_is_cap = bool(_CAP_WORD.match(next_word))
            cur_is_bridge = bool(PREP.search(word))
            cur_is_short = len(word) <= 2

            if next_is_cap and not cur_is_bridge and not cur_is_short:
                phrase = ' '.join(current).strip()
                if is_valid(phrase):
                    result.append(phrase)
                current = []

    if current:
        phrase = ' '.join(current).strip()
        if is_valid(phrase):
            result.append(phrase)

    return result or [mot]

def split_definitions(text):
    chunks = re.split(r'\.\s+(?=[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ0-9])', text)
    return [c for chunk in chunks if is_valid(c := clean_mot(chunk))]

def _similarity(a, b):
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def align_with_test_cases(ocr_defs, test_cases, threshold=0.40):
    result = []
    for tc in test_cases:
        best_score = 0.0
        best_def = tc['definition']

        for ocr in ocr_defs:
            if ocr['direction'] != tc['direction']:
                continue
            score = _similarity(tc['definition'], ocr['mot'])
            if score > best_score:
                best_score = score
                best_def = ocr['mot']

        result.append({
            **tc,
            'definition': best_def if best_score >= threshold else tc['definition'],
            'ocr_score': round(best_score, 2)
        })

    return result

def scan_definitions(nom_image):
    img = cv2.imread(nom_image)
    if img is None:
        raise ValueError(f"Image introuvable : {nom_image}")

    text_h, text_v = ocr_image(img)

    result = []
    for direction, raw in (('H', text_h), ('V', text_v)):
        text = normalize_text(raw)
        text = _clean_section_text(text)

        for definition in split_definitions(text):
            for sub in split_on_capitals(definition):
                sub = clean_mot(sub)
                if is_valid(sub):
                    result.append({'mot': sub, 'direction': direction})

    return result

def scan_and_align(nom_image, test_cases, threshold=0.40):
    ocr_defs = scan_definitions(nom_image)
    return align_with_test_cases(ocr_defs, test_cases, threshold=threshold)
