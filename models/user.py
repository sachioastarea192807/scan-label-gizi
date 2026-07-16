from database import db

from flask_login import UserMixin

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash


class User(

    db.Model,

    UserMixin

):

    __tablename__="users"


    id=db.Column(

        db.Integer,

        primary_key=True

    )


    nama=db.Column(

        db.String(100),

        nullable=False

    )


    email=db.Column(

        db.String(100),

        unique=True,

        nullable=False

    )


    password=db.Column(

        db.String(255),

        nullable=False

    )


    photo=db.Column(

        db.String(255),

        nullable=True

    )


    tinggi_badan=db.Column(

        db.Float,

        nullable=True

    )


    berat_badan=db.Column(

        db.Float,

        nullable=True

    )


    umur=db.Column(

        db.Integer,

        nullable=True

    )


    created_at=db.Column(

        db.DateTime,

        server_default=db.func.now()

    )


    scan_history=db.relationship(

        "ScanHistory",

        back_populates="user",

        cascade="all, delete-orphan"

    )

    def set_password(

        self,

        password

    ):

        self.password=generate_password_hash(

            password

        )


    def check_password(

        self,

        password

    ):

        return check_password_hash(

            self.password,

            password

        )