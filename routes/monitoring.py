import io
from datetime import datetime

from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import url_for
from flask import flash
from flask import send_file

from flask_login import login_required
from flask_login import current_user

from sqlalchemy import func

from database import db

from models.scan_history import ScanHistory
from models.nutrition_result import NutritionResult

monitoring = Blueprint(
    "monitoring",
    __name__
)

# TARGET AKG HARIAN
TARGET = {
    "energi": 2150,
    "protein": 60,
    "lemak_total": 67,
    "karbohidrat_total": 325,
    "gula_total": 50,
    "natrium": 2000
}

# HITUNG PROGRESS
def progress(value, target):

    value = float(value or 0)

    percent = (value / target) * 100

    if percent > 100:
        percent = 100

    return round(percent, 2)


# AMBIL RINGKASAN NUTRISI HARI INI (dipakai monitoring & PDF)
def get_today_summary(user_id):

    nutrition = (

        db.session.query(
            func.sum(NutritionResult.energi),
            func.sum(NutritionResult.protein),
            func.sum(NutritionResult.lemak_total),
            func.sum(NutritionResult.karbohidrat_total),
            func.sum(NutritionResult.gula_total),
            func.sum(NutritionResult.natrium)
        )

        .join(

            ScanHistory,

            NutritionResult.scan_id == ScanHistory.id

        )

        .filter(

            ScanHistory.user_id == user_id

        )

        .filter(

            func.date(
                ScanHistory.created_at
            ) == func.current_date()

        )

        .first()

    )

    nutrition = tuple(
        x if x is not None else 0
        for x in (nutrition or (0, 0, 0, 0, 0, 0))
    )

    meals = (

        ScanHistory.query

        .filter_by(
            user_id=user_id
        )

        .filter(

            func.date(
                ScanHistory.created_at
            ) == func.current_date()

        )

        .order_by(
            ScanHistory.created_at.asc()
        )

        .all()

    )

    return nutrition, meals

# MONITORING
@monitoring.route("/monitoring")
@login_required
def index():

    nutrition, meals = get_today_summary(current_user.id)

    progress_data = {
        "energi": progress(nutrition[0], TARGET["energi"]),
        "protein": progress(nutrition[1], TARGET["protein"]),
        "lemak_total": progress(nutrition[2], TARGET["lemak_total"]),
        "karbohidrat_total": progress(nutrition[3], TARGET["karbohidrat_total"]),
        "gula_total": progress(nutrition[4], TARGET["gula_total"]),
        "natrium": progress(nutrition[5], TARGET["natrium"])
    }

    grouped_meals = {
        "Sarapan": [],
        "Siang": [],
        "Malam": [],
        "Snack": []
    }

    for item in meals:

        grouped_meals[item.meal_type].append(item)

    alerts = []

    if float(nutrition[0] or 0) > TARGET["energi"]:

        alerts.append(
            "Kalori hari ini melebihi batas."
        )

    if float(nutrition[4] or 0) > TARGET["gula_total"]:

        alerts.append(
            "Asupan gula terlalu tinggi."
        )

    if float(nutrition[5] or 0) > TARGET["natrium"]:

        alerts.append(
            "Asupan natrium terlalu tinggi."
        )

    return render_template(

        "user/monitoring.html",

        nutrition=nutrition,

        meals=meals,

        grouped_meals=grouped_meals,

        progress_data=progress_data,

        target=TARGET,

        alerts=alerts

    )


# EXPORT PDF MONITORING (ReportLab)
@monitoring.route("/monitoring/export-pdf")
@login_required
def export_pdf():

    try:

        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.units import cm
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet

        nutrition, meals = get_today_summary(current_user.id)

        styles = getSampleStyleSheet()

        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=2 * cm,
            bottomMargin=2 * cm
        )

        elements = []

        elements.append(
            Paragraph("Laporan Monitoring Nutrisi Harian", styles["Title"])
        )

        elements.append(
            Paragraph(
                f"Nama: {current_user.nama} &nbsp;&nbsp;|&nbsp;&nbsp; "
                f"Tanggal: {datetime.now().strftime('%d %B %Y')}",
                styles["Normal"]
            )
        )

        elements.append(Spacer(1, 0.5 * cm))

        # Ringkasan + Progress AKG
        labels = {
            "energi": ("Energi", "kkal"),
            "protein": ("Protein", "g"),
            "lemak_total": ("Lemak Total", "g"),
            "karbohidrat_total": ("Karbohidrat Total", "g"),
            "gula_total": ("Gula Total", "g"),
            "natrium": ("Natrium", "mg")
        }

        keys = list(labels.keys())

        table_data = [["Komponen", "Total Hari Ini", "Target AKG", "Progress (%)"]]

        for index_key, key in enumerate(keys):

            value = float(nutrition[index_key] or 0)

            target_value = TARGET[key]

            percent = progress(value, target_value)

            table_data.append([
                labels[key][0],
                f"{value} {labels[key][1]}",
                f"{target_value} {labels[key][1]}",
                f"{percent}%"
            ])

        summary_table = Table(
            table_data,
            colWidths=[5 * cm, 4 * cm, 4 * cm, 3 * cm]
        )

        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#90BE6D")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ]))

        elements.append(Paragraph("Progress AKG Hari Ini", styles["Heading2"]))
        elements.append(summary_table)
        elements.append(Spacer(1, 0.7 * cm))

        # Riwayat Scan Hari Ini
        elements.append(Paragraph("Riwayat Scan Hari Ini", styles["Heading2"]))

        history_data = [["Jam", "Produk", "Jenis", "Energi (kkal)"]]

        for item in meals:

            energi_value = (
                item.nutrition_result.energi
                if item.nutrition_result else 0
            )

            history_data.append([
                item.created_at.strftime("%H:%M"),
                item.product_name or "-",
                item.meal_type,
                f"{energi_value}"
            ])

        if len(history_data) == 1:
            history_data.append(["-", "Belum ada scan hari ini", "-", "-"])

        history_table = Table(
            history_data,
            colWidths=[2.5 * cm, 6.5 * cm, 3 * cm, 4 * cm]
        )

        history_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37371F")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(history_table)
        elements.append(Spacer(1, 0.7 * cm))

        # Saran
        saran = []

        if float(nutrition[0] or 0) > TARGET["energi"]:
            saran.append("Kurangi asupan kalori pada sisa hari ini.")

        if float(nutrition[4] or 0) > TARGET["gula_total"]:
            saran.append("Batasi konsumsi makanan/minuman manis.")

        if float(nutrition[5] or 0) > TARGET["natrium"]:
            saran.append("Kurangi makanan tinggi garam/natrium.")

        if not saran:
            saran.append("Asupan nutrisi hari ini masih dalam batas wajar. Pertahankan!")

        elements.append(Paragraph("Saran", styles["Heading2"]))

        for item in saran:
            elements.append(Paragraph(f"- {item}", styles["Normal"]))

        doc.build(elements)

        buffer.seek(0)

        filename = f"monitoring_{datetime.now().strftime('%Y%m%d')}.pdf"

        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )

    except Exception as e:

        print(f"[ERROR] Gagal membuat PDF monitoring untuk user {current_user.id}: {e}")

        flash(
            "Terjadi kendala saat membuat PDF. Silakan coba lagi.",
            "danger"
        )

        return redirect(
            url_for("monitoring.index")
        )


# HAPUS DATA MONITORING HARI INI
@monitoring.route("/monitoring/clear-today", methods=["POST"])
@login_required
def clear_today():

    try:

        _, meals = get_today_summary(current_user.id)

        for item in meals:
            db.session.delete(item)

        db.session.commit()

    except Exception as e:

        print(f"[ERROR] Gagal menghapus data monitoring untuk user {current_user.id}: {e}")

        db.session.rollback()

        flash(
            "Terjadi kendala saat menghapus data.",
            "danger"
        )

        return redirect(
            url_for("monitoring.index")
        )

    flash(
        "Data monitoring hari ini berhasil dihapus.",
        "success"
    )

    return redirect(
        url_for("monitoring.index")
    )