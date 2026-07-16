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
def resize_image(image, target_width=1800):
    h, w = image.shape[:2]
    if w < target_width:
        ratio = target_width / w
        image = cv2.resize(
            image,
            (int(w * ratio), int(h * ratio)),
            interpolation=cv2.INTER_CUBIC
        )

    elif w > target_width:
        ratio = target_width / w
        image = cv2.resize(
            image,
            (target_width, int(h * ratio)),
            interpolation=cv2.INTER_AREA
        )
    return image

# GRAYSCALE
def grayscale(image):
    return cv2.cvtColor(
        image,
        cv2.COLOR_BGR2GRAY
    )

# CLAHE
def apply_clahe(gray):
    clahe = cv2.createCLAHE(
        clipLimit=3.0,
        tileGridSize=(8,8)
    )
    return clahe.apply(gray)

# SHADOW REMOVAL
def remove_shadow(gray):
    dilated = cv2.dilate(
        gray,
        np.ones((7,7), np.uint8)
    )
    bg = cv2.medianBlur(
        dilated,
        21
    )
    diff = 255 - cv2.absdiff(gray, bg)
    norm = cv2.normalize(
        diff,
        None,
        0,
        255,
        cv2.NORM_MINMAX
    )
    return norm

# SHARPEN
def sharpen(gray):
    kernel = np.array([
        [-1,-1,-1],
        [-1,9,-1],
        [-1,-1,-1]
    ])
    return cv2.filter2D(
        gray,
        -1,
        kernel
    )

# DENOISE
def denoise(gray):
    return cv2.fastNlMeansDenoising(
        gray,
        None,
        10,
        7,
        21
    )

# DESKEW
def deskew(image):
    coords = np.column_stack(
        np.where(image < 255)
    )

    if len(coords) < 20:
        return image

    angle = cv2.minAreaRect(coords)[-1]

    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
        
    if abs(angle) < 0.5:
        return image
    
    h, w = image.shape[:2]
    M = cv2.getRotationMatrix2D(
        (w//2,h//2),
        angle,
        1.0
    )

    return cv2.warpAffine(
        image,
        M,
        (w,h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE
    )

# ADAPTIVE
def adaptive(gray):
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        15
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

# MORPH CLOSE
def morphology(img):
    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (2,2)
    )

    return cv2.morphologyEx(
        img,
        cv2.MORPH_CLOSE,
        kernel
    )

# SAVE IMAGE
def save_image(image, path):
    cv2.imwrite(path, image)

# PIPELINE
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
    clahe = apply_clahe(gray)
    shadow = remove_shadow(clahe)
    sharp = sharpen(shadow)
    clean = denoise(sharp)
    clean = deskew(clean)
    adaptive_img = adaptive(clean)
    adaptive_img = morphology(adaptive_img)
    otsu_img = otsu(clean)
    otsu_img = morphology(otsu_img)
    
    variants = {
        "clahe": clahe,
        "adaptive": adaptive_img,
        "otsu": otsu_img
    }

    result = {}

    for name, img in variants.items():
        path = os.path.join(
            output_folder,
            f"{name}_{filename}"
        )

        save_image(
            img,
            path
        )

        result[name] = path

    return result