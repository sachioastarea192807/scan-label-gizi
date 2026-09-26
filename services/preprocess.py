import os
import cv2
import numpy as np

# IMAGE LOADER
def load_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise Exception("Gagal membaca gambar.")
    return image

# AUTO RESIZE
def resize_image(image, target_width=1000):
    h, w = image.shape[:2]
    if w == target_width:
        return image

    ratio = target_width / w
    interpolation = cv2.INTER_CUBIC if w < target_width else cv2.INTER_AREA

    return cv2.resize(
        image,
        (target_width, int(h * ratio)),
        interpolation=interpolation
    )

# GRAYSCALE
def grayscale(image):
    return cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

# OTSU
def otsu(gray):
    _, img = cv2.threshold(
        gray,
        0,
        255,
        cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )
    return img

# SAVE IMAGE
def save_image(image, path):
    cv2.imwrite(path, image)

# PIPELINE RINGAN
def preprocess_image(
        image_path,
        output_folder
):

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    filename = os.path.basename(image_path)
    image = load_image(image_path)
    image = resize_image(image)
    gray = grayscale(image)
    otsu_img = otsu(gray)

    path = os.path.join(
        output_folder,
        f"otsu_{filename}"
    )

    save_image(
        otsu_img,
        path
    )

    return {"otsu": path}