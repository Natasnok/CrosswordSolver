import cv2
import pytesseract
import re
import os

direction = 'V'

def clean_ocr(text):
    replacements = {
        'z.': '2.', 'Z.': '2.',
        's.': '5.', 'S.': '5.',
        'g.': '9.', 'G.': '9.'
    }

    def replace(match):
        return replacements.get(match.group(), match.group())

    text = re.sub(r'[zZgGsS]\.', replace, text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def split_num_def(blocks: list[str]):
    result = []

    for block in blocks:
        block = block.strip()

        if not block:
            continue
        blocklower = block.lower()
        if "horizontalement" in blocklower:
            result.append(('SENS', 'H'))
        elif "verticalement" in blocklower:
            result.append(('SENS', 'V'))

        matches = re.findall(
            r'((?:\d+|[IVXLCDMH]+))\.\s*(.*?)(?=\s+(?:\d+|[IVXLCDMH]+)\.|$)',
            block,
            flags=re.IGNORECASE
        )
        
        for num, definition in matches:
            for defs in definition.split("."):
                if defs != '':
                    result.append(
                        (num.strip(), defs.strip())
                    )
    return result

def split_direction_M(text):
    global direction
    res = []
    
    for bloc in text:
        if not bloc:
            continue
        if bloc[0] == 'SENS':
            direction = bloc[1]
            continue
        res.append({
            "num": bloc[0],
            "mot": bloc[1],
            "direction": direction
        })  
    return res


def split_direction(text, mode):
    match mode:
        case "M":
            text = split_num_def(text)
            res = split_direction_M(text)
            return res
    return []


def scan_definitions(nom_image, mode):
    tesseract_cmd = os.getenv("TESSERACT_CMD")
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    img = cv2.imread(nom_image)
    if img is None:
        raise ValueError(f"Image introuvable : {nom_image}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    text = pytesseract.image_to_string(gray, lang="fra", config="--psm 4")

    raw_text = text.split("\n\n")
    clean_text = [bloc.replace("\n", " ").strip() for bloc in raw_text if bloc.strip()]
    #print(clean_text)
    return split_direction(clean_text, mode)