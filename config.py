import os

from dotenv import load_dotenv

load_dotenv()  # baca .env kalau ada; kalau tidak ada, pakai default di bawah

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def _str_to_bool(value):

    return str(value).strip().lower() in ("1", "true", "yes", "on")

class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "ganti_dengan_secret_key"
    )

    DEBUG = _str_to_bool(os.environ.get("FLASK_DEBUG", "False"))

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://root:@localhost/ocr"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS=False

    UPLOAD_FOLDER="static/uploads"

    # batas ukuran file upload 10MB
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

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