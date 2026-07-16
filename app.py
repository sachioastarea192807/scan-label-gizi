from flask import Flask

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


# Proteksi CSRF untuk semua form POST (login, register, edit
# profil, dst). Semua form sudah punya {{ csrf_token() }}.
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


# Create Database

with app.app_context():

    db.create_all()


if __name__ == "__main__":

    app.run(
        debug=Config.DEBUG
    )