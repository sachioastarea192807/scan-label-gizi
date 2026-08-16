from flask import Flask
from flask import flash
from flask import redirect
from flask import url_for
from flask import render_template

from config import Config
from database import db

from flask_login import LoginManager
from flask_wtf import CSRFProtect

# Import Model
from models.user import User

# Import Blueprint
from routes.home import home
from routes.auth import auth
from routes.dashboard import dashboard
from routes.ocr import ocr
from routes.history import history
from routes.monitoring import monitoring
from routes.profile import profile


app = Flask(__name__)

app.config.from_object(Config)

db.init_app(app)

# Proteksi CSRF untuk semua form POST (login, register, edit profil, dst).
csrf = CSRFProtect(app)

# Login Manager
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Silakan login terlebih dahulu."
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))

# Register Blueprint
app.register_blueprint(home)
app.register_blueprint(auth)
app.register_blueprint(dashboard)
app.register_blueprint(ocr)
app.register_blueprint(history)
app.register_blueprint(monitoring)
app.register_blueprint(profile)

# File upload melebihi MAX_CONTENT_LENGTH 
@app.errorhandler(413)
def file_terlalu_besar(e):
    flash("Ukuran gambar terlalu besar (maksimal 10MB). Silakan gunakan foto dengan ukuran lebih kecil.", "danger")
    return redirect(url_for("ocr.upload_page"))

# 404 - halaman/data tidak ditemukan
@app.errorhandler(404)
def halaman_tidak_ditemukan(e):
    return render_template("errors/404.html"), 404

# Create Database
with app.app_context():

    db.create_all()

if __name__ == "__main__":

    app.run(
        debug=Config.DEBUG
    )