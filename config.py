import os

from dotenv import load_dotenv

load_dotenv()  # baca .env kalau ada; kalau tidak ada, pakai default di bawah

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def _str_to_bool(value):

    return str(value).strip().lower() in ("1", "true", "yes", "on")


class Config:

    # Fallback ini cuma jaring pengaman kalau .env tidak ada -
    # jangan diandalkan, selalu isi SECRET_KEY di .env
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "ganti_dengan_secret_key"
    )

    # Diset lewat FLASK_DEBUG di .env
    DEBUG = _str_to_bool(os.environ.get("FLASK_DEBUG", "False"))

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:@localhost/ocr"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS=False

    UPLOAD_FOLDER="static/uploads"

    # Cuma dipakai kalau file ini benar-benar ada (dicek di
    # services/ocr_engine.py). Kosongkan/abaikan kalau Tesseract
    # sudah ada di PATH sistem.
    TESSERACT_CMD = r"C:\Users\Angelia Salsabila\tesseract_ocr\tesseract.exe"
    
    ORIGINAL_FOLDER = os.path.join(
        BASE_DIR,
        "static",
        "uploads",
        "original"
    )

    PREPROCESS_FOLDER = os.path.join(
        BASE_DIR,
        "static",
        "uploads",
        "preprocess"
    )

    RESULT_FOLDER = os.path.join(
        BASE_DIR,
        "static",
        "uploads",
        "result"
    )

    PROFILE_FOLDER = os.path.join(
        BASE_DIR,
        "static",
        "uploads",
        "profile"
    )