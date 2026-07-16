import os
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    flash,
    url_for
)

from flask_login import (
    login_required,
    current_user
)

from werkzeug.utils import secure_filename

from config import Config
from database import db
from models.user import User
from models.scan_history import ScanHistory

profile = Blueprint(
    "profile",
    __name__
)

ALLOWED_PHOTO_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_photo(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_PHOTO_EXTENSIONS
    )


def parse_number(value, cast=float):

    if value is None or str(value).strip() == "":

        return None

    try:

        return cast(value)

    except (TypeError, ValueError):

        return None


@profile.route("/profile")
@login_required
def index():

    total_scan = ScanHistory.query.filter_by(
        user_id=current_user.id
    ).count()

    last_scan = (
        ScanHistory.query
        .filter_by(user_id=current_user.id)
        .order_by(
            ScanHistory.created_at.desc()
        )
        .first()
    )

    return render_template(
        "user/profile.html",
        user=current_user,
        total_scan=total_scan,
        last_scan=last_scan
    )


@profile.route(
    "/profile/edit",
    methods=["GET", "POST"]
)
@login_required
def edit():

    if request.method == "POST":

        # Cek apakah email sudah dipakai

        user = User.query.filter_by(
            email=request.form["email"]
        ).first()

        if user and user.id != current_user.id:

            flash(
                "Email sudah digunakan.",
                "danger"
            )

            return redirect(
                url_for("profile.edit")
            )

        # Update foto profil (opsional)

        photo_file = request.files.get("photo")

        if photo_file and photo_file.filename:

            if not allowed_photo(photo_file.filename):

                flash(
                    "Format foto tidak didukung (gunakan JPG/PNG).",
                    "danger"
                )

                return redirect(
                    url_for("profile.edit")
                )

            filename = secure_filename(photo_file.filename)

            extension = filename.rsplit(".", 1)[1]

            new_filename = f"{uuid.uuid4()}.{extension}"

            photo_folder = Config.PROFILE_FOLDER

            os.makedirs(photo_folder, exist_ok=True)

            photo_file.save(
                os.path.join(photo_folder, new_filename)
            )

            current_user.photo = f"uploads/profile/{new_filename}"

        # Update data

        current_user.nama = request.form["nama"]

        current_user.email = request.form["email"]

        # Update detail pribadi (opsional)

        current_user.tinggi_badan = parse_number(
            request.form.get("tinggi_badan"), float
        )

        current_user.berat_badan = parse_number(
            request.form.get("berat_badan"), float
        )

        current_user.umur = parse_number(
            request.form.get("umur"), int
        )

        db.session.commit()

        flash(
            "Profil berhasil diperbarui.",
            "success"
        )

        return redirect(
            url_for("profile.index")
        )

    return render_template(
        "user/edit_profile.html",
        user=current_user
    )


@profile.route(
    "/profile/password",
    methods=["GET", "POST"]
)
@login_required
def change_password():

    if request.method == "POST":

        old = request.form["old_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]

        if not current_user.check_password(old):

            flash(
                "Password lama salah.",
                "danger"
            )

            return redirect(
                url_for("profile.change_password")
            )

        if new != confirm:

            flash(
                "Konfirmasi password tidak sesuai.",
                "danger"
            )

            return redirect(
                url_for("profile.change_password")
            )

        if len(new) < 6:

            flash(
                "Password baru minimal 6 karakter.",
                "danger"
            )

            return redirect(
                url_for("profile.change_password")
            )

        current_user.set_password(new)

        db.session.commit()

        flash(
            "Password berhasil diubah.",
            "success"
        )

        return redirect(
            url_for("profile.index")
        )

    return render_template(
        "user/change_password.html"
    )