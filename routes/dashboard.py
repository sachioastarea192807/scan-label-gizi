from flask import Blueprint
from flask import render_template
from flask import flash

from flask_login import login_required
from flask_login import current_user

from sqlalchemy import func

from database import db

from models.scan_history import ScanHistory
from models.nutrition_result import NutritionResult


dashboard = Blueprint(
    "dashboard",
    __name__
)


@dashboard.route("/dashboard")
@login_required
def index():

    try:

        total_scan = ScanHistory.query.filter_by(
            user_id=current_user.id
        ).count()

        nutrition = db.session.query(

            func.sum(NutritionResult.energi),

            func.sum(NutritionResult.protein),

            func.sum(NutritionResult.lemak_total),

            func.sum(NutritionResult.karbohidrat_total),

            func.sum(NutritionResult.gula_total),

            func.sum(NutritionResult.natrium)

        ).join(

            ScanHistory,

            NutritionResult.scan_id == ScanHistory.id

        ).filter(

            ScanHistory.user_id == current_user.id

        ).filter(

            func.date(
                ScanHistory.created_at
            ) == func.current_date()

        ).first()

        if nutrition is None:

            nutrition = (0, 0, 0, 0, 0, 0)

        nutrition = tuple(
            x if x is not None else 0
            for x in nutrition
        )

        latest = ScanHistory.query.filter_by(

            user_id=current_user.id

        ).order_by(

            ScanHistory.created_at.desc()

        ).limit(5).all()

    except Exception as e:

        print(f"[ERROR] Gagal memuat dashboard untuk user {current_user.id}: {e}")

        flash(
            "Terjadi kendala saat memuat data dashboard.",
            "danger"
        )

        total_scan = 0
        nutrition = (0, 0, 0, 0, 0, 0)
        latest = []

    return render_template(

        "user/dashboard.html",

        total_scan=total_scan,

        latest=latest,

        nutrition=nutrition

    )