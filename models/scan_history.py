from database import db


class ScanHistory(db.Model):

    __tablename__ = "scan_history"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    product_name = db.Column(
        db.String(150),
        nullable=True
    )

    original_image = db.Column(
        db.String(255),
        nullable=False
    )

    preprocess_image = db.Column(
        db.String(255),
        nullable=False
    )

    raw_text = db.Column(
        db.Text,
        nullable=True
    )

    cleaned_text = db.Column(
        db.Text,
        nullable=True
    )

    # confidence rata-rata OCR (0-100), dipakai untuk badge "Perlu dicek"
    ocr_confidence = db.Column(
        db.Float,
        nullable=True,
        default=0
    )

    # true kalau user sempat mengoreksi manual sebelum simpan
    manually_corrected = db.Column(
        db.Boolean,
        default=False
    )

    meal_type = db.Column(

        db.Enum(

            "Sarapan",

            "Siang",

            "Malam",

            "Snack",

            name="meal_type_enum"

        ),

        nullable=False,

        default="Snack"

    )

    created_at = db.Column(

        db.DateTime,

        server_default=db.func.now()

    )

    # RELATIONSHIP

    user = db.relationship(

        "User",

        back_populates="scan_history"

    )

    nutrition_result = db.relationship(

        "NutritionResult",

        back_populates="scan",

        uselist=False,

        cascade="all, delete-orphan"

    )

    def __repr__(self):

        return f"<ScanHistory {self.id}>"