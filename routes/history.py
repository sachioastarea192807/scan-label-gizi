from flask import Blueprint
from flask import render_template
from flask import request
from flask import redirect
from flask import url_for
from flask import flash
from flask import session
from flask import abort

from flask_login import login_required
from flask_login import current_user

from database import db

from models.scan_history import ScanHistory
from models.nutrition_result import NutritionResult

history = Blueprint(
    "history",
    __name__
)

NUTRITION_NUMERIC_FIELDS = [
    "energi",
    "protein",
    "lemak_total",
    "lemak_jenuh",
    "lemak_trans",
    "kolesterol",
    "karbohidrat_total",
    "serat",
    "gula_total",
    "sukrosa",
    "natrium"
]

# HALAMAN RIWAYAT
@history.route("/history")
@login_required
def index():

    query = (
        ScanHistory.query
        .filter_by(
            user_id=current_user.id
        )
    )

    keyword = request.args.get("q", "").strip()

    if keyword:

        query = query.filter(
            ScanHistory.product_name.ilike(f"%{keyword}%")
        )

    meal_type = request.args.get("meal_type", "").strip()

    if meal_type:

        query = query.filter(
            ScanHistory.meal_type == meal_type
        )

    histories = (
        query
        .order_by(
            ScanHistory.created_at.desc()
        )
        .all()
    )

    return render_template(
        "user/history.html",
        histories=histories,
        keyword=keyword,
        meal_type=meal_type
    )

# DETAIL RIWAYAT
@history.route("/history/<int:history_id>")
@login_required
def detail(history_id):

    item = ScanHistory.query.filter_by(
        id=history_id,
        user_id=current_user.id
    ).first()

    if item is None:
        abort(404)

    return render_template(
        "user/history_detail.html",
        item=item
    )

# HAPUS RIWAYAT
@history.route("/history/delete/<int:history_id>", methods=["POST"])
@login_required
def delete(history_id):

    item = ScanHistory.query.filter_by(
        id=history_id,
        user_id=current_user.id
    ).first()

    if item is None:
        abort(404)

    db.session.delete(item)
    db.session.commit()

    flash(
        "Riwayat berhasil dihapus.",
        "success"
    )

    return redirect(
        url_for("history.index")
    )

# BANGUN DATA DARI FORM 
def build_scan_payload(form):

    payload = {

        "product_name": form.get("product_name") or "Produk Tanpa Nama",

        "meal_type": form.get("meal_type") or "Snack",

        "original_image": form.get("original_image"),

        "preprocess_image": form.get("preprocess_image"),

        "raw_text": form.get("raw_text"),

        "cleaned_text": form.get("cleaned_text"),

        "ocr_confidence": float(form.get("ocr_confidence") or 0),

        "serving_size": form.get("serving_size") or None,

        "serving_per_container": form.get("serving_per_container") or None

    }

    for field_name in NUTRITION_NUMERIC_FIELDS:

        payload[field_name] = float(form.get(field_name) or 0)

    return payload

# SIMPAN KE DATABASE
def save_scan(payload, user_id):

    scan = ScanHistory(

        user_id=user_id,

        product_name=payload["product_name"],

        meal_type=payload["meal_type"],

        original_image=payload["original_image"],

        preprocess_image=payload["preprocess_image"],

        raw_text=payload["raw_text"],

        cleaned_text=payload["cleaned_text"],

        ocr_confidence=payload["ocr_confidence"],

        manually_corrected=payload.get("manually_corrected", False)

    )

    db.session.add(scan)
    db.session.commit()

    nutrition = NutritionResult(

        scan_id=scan.id,

        serving_size=payload["serving_size"],

        serving_per_container=payload["serving_per_container"],

        **{key: payload[key] for key in NUTRITION_NUMERIC_FIELDS}

    )

    db.session.add(nutrition)
    db.session.commit()

    return scan

# simpan hasil scan. kalau belum login, ditunda dulu di session lalu diarahkan ke login
@history.route("/save-result", methods=["POST"])
def save_result():

    try:

        payload = build_scan_payload(request.form)

    except (TypeError, ValueError) as e:

        print(f"[ERROR] Gagal membaca data hasil scan: {e}")

        flash(
            "Data hasil scan tidak valid. Silakan periksa kembali nilai yang diisi.",
            "danger"
        )

        return redirect(
            url_for("ocr.upload_page")
        )

    if current_user.is_authenticated:

        try:

            save_scan(payload, current_user.id)

        except Exception as e:

            print(f"[ERROR] Gagal menyimpan riwayat untuk user {current_user.id}: {e}")

            db.session.rollback()

            flash(
                "Terjadi kendala saat menyimpan riwayat. Silakan coba lagi.",
                "danger"
            )

            return redirect(
                url_for("ocr.upload_page")
            )

        flash(
            "Riwayat berhasil disimpan.",
            "success"
        )

        return redirect(
            url_for("history.index")
        )

    # Belum login akan simpan sementara di session
    session["pending_scan"] = payload

    flash(
        "Silakan login untuk menyimpan hasil scan ini. "
        "Hasil Anda tetap aman dan akan otomatis tersimpan setelah login.",
        "info"
    )

    return redirect(
        url_for("auth.login")
    )