import os
import cv2
import pytesseract
import concurrent.futures

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

# panggilan pytesseract di proses subprocess terpisah 
MAX_WORKERS = min(8, (os.cpu_count() or 4) * 2)

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
    
    loaded = [load_image(path) for path in images.values()]

    all_candidates = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [
            executor.submit(run_ocr, image, psm)
            for image in loaded
            for psm in PSM_LIST
        ]

        for future in concurrent.futures.as_completed(futures):
            try:
                all_candidates.append(future.result())
            except Exception:
                pass

    best = choose_best(all_candidates)

    return best