from database import db


class NutritionResult(db.Model):

    __tablename__ = "nutrition_result"

    id = db.Column(

        db.Integer,

        primary_key=True

    )

    scan_id = db.Column(

        db.Integer,

        db.ForeignKey("scan_history.id"),

        nullable=False,

        unique=True

    )

    energi = db.Column(
        db.DECIMAL(8, 2),
        default=0
    )

    protein = db.Column(
        db.DECIMAL(8, 2),
        default=0
    )

    # Lemak dipecah sesuai struktur label BPOM

    lemak_total = db.Column(
        db.DECIMAL(8, 2),
        default=0
    )

    lemak_jenuh = db.Column(
        db.DECIMAL(8, 2),
        default=0
    )

    lemak_trans = db.Column(
        db.DECIMAL(8, 2),
        default=0
    )

    kolesterol = db.Column(
        db.DECIMAL(8, 2),
        default=0
    )

    # Karbohidrat dipecah sesuai struktur label BPOM

    karbohidrat_total = db.Column(
        db.DECIMAL(8, 2),
        default=0
    )

    serat = db.Column(
        db.DECIMAL(8, 2),
        default=0
    )

    gula_total = db.Column(
        db.DECIMAL(8, 2),
        default=0
    )

    sukrosa = db.Column(
        db.DECIMAL(8, 2),
        default=0
    )

    natrium = db.Column(
        db.DECIMAL(8, 2),
        default=0
    )

    serving_size = db.Column(
        db.String(50),
        nullable=True
    )

    serving_per_container = db.Column(
        db.String(50),
        nullable=True
    )

    scan = db.relationship(

        "ScanHistory",

        back_populates="nutrition_result"

    )

    def __repr__(self):

        return f"<NutritionResult {self.id}>"