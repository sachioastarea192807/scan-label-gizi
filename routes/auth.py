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

        nama = request.form["nama"]

        email = request.form["email"]

        password = request.form["password"]

        # Cek email
        if User.query.filter_by(email=email).first():

            flash(
                "Email sudah digunakan.",
                "danger"
            )

            return redirect(
                url_for("auth.register")
            )

        # Buat user baru
        user = User(

            nama=nama,

            email=email

        )

        # Hash password
        user.set_password(password)

        db.session.add(user)

        db.session.commit()

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

        email = request.form["email"]

        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and user.check_password(password):

            login_user(user)

            # auto-save hasil scan tamu yang tertunda (lihat routes/history.py:save_result)
            pending_scan = session.pop("pending_scan", None)

            if pending_scan:

                save_scan(pending_scan, user.id)

                flash(
                    "Login berhasil. Hasil scan Anda otomatis tersimpan ke riwayat.",
                    "success"
                )

                return redirect(
                    url_for("history.index")
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