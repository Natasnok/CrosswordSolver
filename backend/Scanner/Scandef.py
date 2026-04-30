import cv2
import pytesseract
import numpy as np
import re


OCR_TYPOS = {
    r'\btunnet\b': 'tunnel',
    r'\bsk\b': 'ski',
    r'\bCapitate\b': 'Capitale',
    r'\binventeur\b': 'Inventeur',
    r'\bGl\b': 'GI',
}


PREP = (
    r'\b(?:de|des|du|le|la|les|à|au|aux|en|par|sur|un|une|et|ou|'
    r'se|ce|ne|y|qu|dont|Nations|Saint|Sainte|Mont|Col|Lac)$'
)


def preprocess_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.fastNlMeansDenoising(gray, h=20)

    coords = np.column_stack(np.where(gray < 128))
    if len(coords) > 0:
        angle = cv2.minAreaRect(coords)[-1]
        angle = -(90 + angle) if angle < -45 else -angle

        if abs(angle) > 0.5:
            h, w = gray.shape
            M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
            gray = cv2.warpAffine(
                gray,
                M,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )

    gray = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        51,
        15
    )
    return gray


def best_psm_text(gray):
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    best_text = ""
    for psm in [3, 4, 6, 11]:
        text = pytesseract.image_to_string(gray, lang="fra", config=f"--psm {psm}")
        if len(text.strip()) > len(best_text.strip()):
            best_text = text

    return best_text


def fix_typos(text: str) -> str:
    for pattern, replacement in OCR_TYPOS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def normalize_text(text: str) -> str:
    text = text.replace('\u2019', "'").replace('\u2018', "'")
    text = text.replace('\n', ' ')
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def remove_short_ocr_artifacts(text: str) -> str:
    # Supprime les mini-résidus OCR du style "Gl." "sk." "Ab."
    # uniquement quand ils sont suivis d'un début probable de nouvelle définition
    text = re.sub(
        r'(?<!\w)\b[A-Za-zÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ]{1,2}\.(?=\s+[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ0-9])',
        ' ',
        text
    )
    return text


def clean_mot(mot: str) -> str:
    mot = mot.strip()

    # Supprime numéros ou chiffres romains au début
    mot = re.sub(r'^(?:\d+|[IVXLCDM]+)\s+', '', mot)

    # Supprime ponctuation parasite en début/fin
    mot = mot.strip(" ,.;:-–—_")

    # Compacte les espaces
    mot = re.sub(r'\s{2,}', ' ', mot)

    return mot.strip()


def is_valid(mot: str) -> bool:
    if len(mot) < 3:
        return False

    # rejette les trucs quasi vides ou sans lettres
    if not re.search(r'[A-Za-zÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸàâäçéèêëîïôöùûüÿ]', mot):
        return False

    return True


def split_on_capitals(mot: str) -> list[str]:
    parts = re.split(r'\s+', mot)
    result = []
    current = []

    for i, word in enumerate(parts):
        current.append(word)

        if i < len(parts) - 1:
            next_word = parts[i + 1]
            next_is_capital = re.match(
                r'^[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ][a-zàâäçéèêëîïôöùûüÿ]',
                next_word
            )
            current_is_prep = re.search(PREP, word, flags=re.IGNORECASE)

            if next_is_capital and not current_is_prep:
                phrase = ' '.join(current).strip()
                if is_valid(phrase):
                    result.append(phrase)
                current = []

    if current:
        phrase = ' '.join(current).strip()
        if is_valid(phrase):
            result.append(phrase)

    return result if result else [mot]


def split_definitions(text: str) -> list[str]:
    # Coupe seulement sur ". " suivi d'une majuscule ou d'un chiffre
    # ex: "Capitale du Pérou. 12. Ville..." ou "Capitale du Pérou. Inventeur..."
    chunks = re.split(
        r'\.\s+(?=[A-ZÀÂÄÇÉÈÊËÎÏÔÖÙÛÜŸ0-9])',
        text
    )

    cleaned = []
    for chunk in chunks:
        chunk = clean_mot(chunk)
        if is_valid(chunk):
            cleaned.append(chunk)

    return cleaned


def extract_sections(raw: str) -> list[tuple[str, str]]:
    parts = re.split(r'VERTICALEMENT', raw, flags=re.IGNORECASE)
    sections = []

    if len(parts) >= 2:
        h_parts = re.split(r'HORIZONTALEMENT', parts[0], flags=re.IGNORECASE)
        horizontal_text = h_parts[1] if len(h_parts) >= 2 else parts[0]
        vertical_text = parts[1]

        sections.append(('H', horizontal_text))
        sections.append(('V', vertical_text))
    else:
        sections.append(('V', raw))

    return sections


def scan_definitions(nom_image):
    img = cv2.imread(nom_image)
    if img is None:
        raise ValueError(f"Image introuvable : {nom_image}")

    gray = preprocess_image(img)
    raw = best_psm_text(gray)
    raw = fix_typos(raw)
    raw = normalize_text(raw)

    result = []
    sections = extract_sections(raw)

    for direction, text in sections:
        # Supprime les numéros de définitions du style "1." "12." "IV."
        text = re.sub(r'\b(?:[IVXLCDM]+|\d+)\s*\.\s*', ' ', text)

        # Supprime petits déchets OCR du style "Gl."
        text = remove_short_ocr_artifacts(text)

        # Recompacte après suppressions
        text = re.sub(r'\s{2,}', ' ', text).strip()

        defs = split_definitions(text)

        for d in defs:
            sub_defs = split_on_capitals(d)

            for sub in sub_defs:
                sub = clean_mot(sub)
                if is_valid(sub):
                    result.append({
                        "mot": sub,
                        "direction": direction
                    })

    return result