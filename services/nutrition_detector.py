import os
import cv2
import numpy as np

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

    # urutkan dari area terbesar, ambil maksimal 5 
    candidates.sort(key=lambda c: c[2]*c[3], reverse=True)
    return candidates[:5]


def detect_table(image):

    gray=cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

    candidates=find_candidates(gray)

    if len(candidates)==0:

        return image

    # ambil langsung kandidat area terbesar, tanpa verifikasi OCR
    x, y, w, h = candidates[0]

    # sedikit padding supaya teks di tepi kotak tidak terpotong
    height, width = gray.shape[:2]

    pad_x = int(w * 0.03)
    pad_y = int(h * 0.03)

    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(width, x + w + pad_x)
    y2 = min(height, y + h + pad_y)

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
    if w > 1200:
        ratio = 1200 / w
        image = cv2.resize(
            image,
            (1200, int(h * ratio)),
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