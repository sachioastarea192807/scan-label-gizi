import os
import cv2
import numpy as np
import pytesseract

HEADER_KEYWORDS = [
    "informasi",
    "nilai",
    "gizi",

    "nutrition",
    "facts",

    "energy",
    "protein",
    "karbohidrat"
]

def find_candidates(gray):

    edges = cv2.Canny(
        gray,
        50,
        150
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (7,7)
    )

    edges = cv2.dilate(
        edges,
        kernel,
        iterations=2
    )

    contours,_ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    candidates=[]

    for c in contours:

        x,y,w,h = cv2.boundingRect(c)

        area=w*h

        if area<80000:
            continue

        ratio=h/w

        # tabel BPOM 
        if ratio<0.25:
            continue

        if ratio>5:
            continue

        candidates.append((x,y,w,h))

    # urutkan dari area terbesar, ambil maksimal 5 biar nggak berat
    candidates.sort(key=lambda c: c[2]*c[3], reverse=True)
    return candidates[:5]


def quick_ocr(image):

    config="--oem 3 --psm 6"

    return pytesseract.image_to_string(
        image,
        lang="ind+eng",
        config=config
    ).lower()

# Lebar maksimum crop kandidat 
SCORING_MAX_WIDTH = 1500

def resize_for_scoring(crop):

    h, w = crop.shape[:2]

    if w <= SCORING_MAX_WIDTH:
        return crop

    ratio = SCORING_MAX_WIDTH / w

    return cv2.resize(
        crop,
        (SCORING_MAX_WIDTH, int(h * ratio)),
        interpolation=cv2.INTER_AREA
    )

def score_text(text):

    score=0

    for word in HEADER_KEYWORDS:

        if word in text:

            score+=1

    return score

# skor 0 = tidak ada kata kunci gizi kebaca sama sekali di kandidat itu
MIN_TABLE_SCORE = 1


def detect_table(image):

    gray=cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    candidates=find_candidates(gray)

    if len(candidates)==0:

        return image

    scored = []

    for x,y,w,h in candidates:

        crop=image[
            y:y+h,
            x:x+w
        ]

        # hanya untuk cek kata kunci crop asli
        scoring_crop = resize_for_scoring(crop)

        text=quick_ocr(scoring_crop)

        score=score_text(text)

        scored.append((score, x, y, w, h))

    relevant = [c for c in scored if c[0] >= MIN_TABLE_SCORE]

    if not relevant:
        
        return image

    # gabungan semua kandidat relevan jadi satu crop 
    x1 = min(c[1] for c in relevant)
    y1 = min(c[2] for c in relevant)
    x2 = max(c[1] + c[3] for c in relevant)
    y2 = max(c[2] + c[4] for c in relevant)

    # sedikit padding supaya teks di tepi kotak tidak terpotong
    height, width = gray.shape[:2]

    pad_x = int((x2 - x1) * 0.03)
    pad_y = int((y2 - y1) * 0.03)

    x1 = max(0, x1 - pad_x)
    y1 = max(0, y1 - pad_y)
    x2 = min(width, x2 + pad_x)
    y2 = min(height, y2 + pad_y)

    return image[y1:y2, x1:x2]

def save_crop(crop,path):

    cv2.imwrite(
        path,
        crop
    )


def detect_nutrition_table(
    image_path,
    output_folder
):

    image=cv2.imread(image_path)

    # resize dulu biar proses deteksi kontur & OCR nggak berat
    h, w = image.shape[:2]
    if w > 1800:
        ratio = 1800 / w
        image = cv2.resize(
            image,
            (1800, int(h * ratio)),
            interpolation=cv2.INTER_AREA
        )

    crop=detect_table(image)

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    # nama file crop mengikuti nama file original
    base_filename = os.path.basename(image_path)

    path=os.path.join(
        output_folder,
        f"crop_{base_filename}"
    )

    save_crop(
        crop,
        path
    )

    return path