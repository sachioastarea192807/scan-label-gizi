import os
import cv2
import pytesseract

from pytesseract import Output
from config import Config

if hasattr(Config, "TESSERACT_CMD"):
    if os.path.exists(Config.TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_CMD

LANGUAGE = "ind+eng"

BASE_CONFIG = (
    "--oem 3 "
    "-c preserve_interword_spaces=1"
)

PSM_LIST = [6, 4, 11]

def load_image(path):
    image = cv2.imread(path)
    if image is None:
        raise Exception(f"Gagal membaca {path}")
    return image

def run_ocr(image, psm):
    config = f"{BASE_CONFIG} --psm {psm}"
    data = pytesseract.image_to_data(
        image,
        lang=LANGUAGE,
        config=config,
        output_type=Output.DICT
    )

    words = []
    confidence = []
    lines = {}
    total = len(data["text"])

    for i in range(total):
        text = data["text"][i].strip()
        try:
            conf = float(data["conf"][i])
        except:
            conf = -1

        if text == "":
            continue

        if conf < 0:
            continue

        words.append({
            "text": text,
            "conf": conf,
            "left": data["left"][i],
            "top": data["top"][i],
            "width": data["width"][i],
            "height": data["height"][i]

        })

        confidence.append(conf)

        # Kelompokkan kata per baris (pakai info yang sudah ada dari
        # image_to_data, tanpa perlu OCR ulang gambar yang sama lewat
        # image_to_string terpisah).
        line_key = (
            data["block_num"][i],
            data["par_num"][i],
            data["line_num"][i]
        )
        lines.setdefault(line_key, []).append(text)

    raw = "\n".join(
        " ".join(line_words)
        for line_words in lines.values()
    )

    avg = sum(confidence)/len(confidence) if confidence else 0

    return {
        "raw_text": raw,
        "words": words,
        "confidence": round(avg,2),
        "word_count": len(words),
        "psm": psm
    }

def process_variant(image):
    candidates = []
    for psm in PSM_LIST:
        try:
            result = run_ocr(image, psm)
            candidates.append(result)
        except:
            pass

    return candidates

def score(candidate):
    score = 0
    score += candidate["confidence"] * 0.7
    score += candidate["word_count"] * 0.3

    return score

def choose_best(candidates):
    if len(candidates)==0:
        return None
    candidates.sort(
        key=score,
        reverse=True
    )

    return candidates[0]

def read_document(images):
    """
    images adalah dict hasil preprocess.py
    {
        gray:...,
        clahe:...,
        shadow:...,
        adaptive:...,
        otsu:...
    }
    """
    all_candidates = []
    
    for _, path in images.items():
        image = load_image(path)
        result = process_variant(image)
        all_candidates.extend(result)
    best = choose_best(all_candidates)

    return best