from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import flash
from flask import url_for

import os
import uuid
from werkzeug.utils import secure_filename

from config import Config

# service pipeline OCR
from services.nutrition_detector import detect_nutrition_table
from services.preprocess import preprocess_image
from services.ocr_engine import read_document
from services.layout_parser import parse_document
from services.validation import validate

ocr = Blueprint(
    "ocr",
    __name__
)

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg"
}

def allowed_file(filename):
    return (
        "." in filename
        and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

# Upload Page
@ocr.route("/upload", methods=["GET"])
def upload_page():
    return render_template(
        "guest/upload.html"
    )

# Process OCR
@ocr.route("/upload", methods=["POST"])
def upload():
    if "image" not in request.files:
        flash("Silakan pilih gambar.", "danger")
        return redirect(url_for("ocr.upload_page"))

    file = request.files["image"]

    if file.filename == "":
        flash("Silakan pilih gambar.", "danger")
        return redirect(url_for("ocr.upload_page"))

    if not allowed_file(file.filename):
        flash("Format gambar tidak didukung.", "danger")
        return redirect(url_for("ocr.upload_page"))

    filename = secure_filename(file.filename)
    extension = filename.rsplit(".", 1)[1]
    new_filename = f"{uuid.uuid4()}.{extension}"

    original_folder = Config.ORIGINAL_FOLDER
    preprocess_folder = Config.PREPROCESS_FOLDER

    os.makedirs(original_folder, exist_ok=True)
    os.makedirs(preprocess_folder, exist_ok=True)

    original_path = os.path.join(
        original_folder,
        new_filename
    )

    # simpan gambar original
    file.save(original_path)

    # jika terjadi error
    try:
        # deteksi & crop tabel nutrisi
        crop_path = detect_nutrition_table(
            original_path,
            preprocess_folder
        )

        # preprocess (multi varian)
        preprocess_paths = preprocess_image(
            crop_path,
            preprocess_folder
        )

        # baca OCR (voting system)
        ocr_result = read_document(preprocess_paths)

        if not ocr_result:
            flash("Gagal membaca teks dari gambar. Silakan pastikan gambar jelas dan tidak buram.")
            return redirect(url_for("ocr.upload_page"))

        raw_text = ocr_result.get("raw_text", "")
        confidence = ocr_result.get("confidence", 0)

        # ekstraksi field per posisi kata (layout parser)
        ocr_words = ocr_result.get("words", [])
        nutrition_data = parse_document(ocr_words)

        # validasi kewajaran nilai (unit, rumus kalori, rentang angka)
        validated_data = validate(nutrition_data)

    except Exception as e:
        print(f"[ERROR] Gagal memproses OCR untuk {new_filename}: {e}")
        flash("Terjadi kendala saat memproses gambar. Silakan coba foto lain, atau ambil ulang dengan pencahayaan lebih terang.", "danger")
        return redirect(url_for("ocr.upload_page"))

    # nama file crop hasil deteksi tabel gizi
    preprocess_filename = os.path.basename(crop_path)

    return render_template(
        "guest/result.html",
        original_image=f"uploads/original/{new_filename}",
        preprocess_image=f"uploads/preprocess/{preprocess_filename}",
        raw_text=raw_text,
        nutrition=validated_data,
        confidence=confidence
    )