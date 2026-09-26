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
    "--oem 3 --psm 6 "
    "-c preserve_interword_spaces=1"
)

def load_image(path):
    image = cv2.imread(path)
    if image is None:
        raise Exception(f"Gagal membaca {path}")
    return image

def run_ocr(image):
    data = pytesseract.image_to_data(
        image,
        lang=LANGUAGE,
        config=BASE_CONFIG,
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
        "confidence": round(avg, 2),
        "word_count": len(words)
    }


def read_document(images):
    first_path = next(iter(images.values()))
    image = load_image(first_path)
    return run_ocr(image)