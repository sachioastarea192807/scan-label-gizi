from flask import (
    Blueprint,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    session
)

from flask_login import (
    login_user,
    logout_user,
    login_required
)

from database import db
from models.user import User
from routes.history import save_scan


auth = Blueprint(
    "auth",
    __name__
)


# REGISTER

@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        nama = request.form.get("nama", "").strip()

        email = request.form.get("email", "").strip()

        password = request.form.get("password", "")

        if not nama or not email or not password:

            flash(
                "Semua kolom wajib diisi.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        # Cek email
        try:

            email_sudah_ada = User.query.filter_by(email=email).first()

        except Exception as e:

            print(f"[ERROR] Gagal query database saat cek email registrasi: {e}")

            flash(
                "Terjadi kendala pada server. Silakan coba lagi beberapa saat lagi.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        if email_sudah_ada:

            flash(
                "Email sudah digunakan.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        try:

            # Buat user baru
            user = User(

                nama=nama,

                email=email

            )

            # Hash password
            user.set_password(password)

            db.session.add(user)

            db.session.commit()

        except Exception as e:

            print(f"[ERROR] Gagal registrasi user {email}: {e}")

            db.session.rollback()

            flash(
                "Terjadi kendala saat mendaftar. Silakan coba lagi.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        flash(
            "Register berhasil. Silakan login.",
            "success"
        )

        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "auth/register.html"
    )


# LOGIN

@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip()

        password = request.form.get("password", "")

        try:

            user = User.query.filter_by(
                email=email
            ).first()

        except Exception as e:

            print(f"[ERROR] Gagal query database saat login: {e}")

            flash(
                "Terjadi kendala pada server. Silakan coba lagi beberapa saat lagi.",
                "danger"
            )

            return redirect(
                url_for("auth.login")
            )

        if user and user.check_password(password):

            login_user(user)

            # auto-save hasil scan tamu yang tertunda
            pending_scan = session.pop("pending_scan", None)

            if pending_scan:

                try:

                    save_scan(pending_scan, user.id)

                    flash(
                        "Login berhasil. Hasil scan Anda otomatis tersimpan ke riwayat.",
                        "success"
                    )

                    return redirect(
                        url_for("history.index")
                    )

                except Exception as e:

                    print(f"[ERROR] Gagal auto-save pending_scan untuk user {user.id}: {e}")

                    db.session.rollback()

                    flash(
                        "Login berhasil, tapi hasil scan sebelumnya gagal disimpan otomatis. Silakan scan ulang.",
                        "warning"
                    )

                    return redirect(
                        url_for("dashboard.index")
                    )

            flash(
                "Login berhasil.",
                "success"
            )

            return redirect(
                url_for("dashboard.index")
            )

        flash(
            "Email atau password salah.",
            "danger"
        )

    return render_template(
        "auth/login.html"
    )


# LOGOUT

@auth.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "Berhasil logout.",
        "success"
    )

    return redirect(
        url_for("home.index")
    )