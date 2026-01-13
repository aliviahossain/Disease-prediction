from backend import db

class Disease(db.Model):
    __tablename__ = "diseases"

    id = db.Column(db.Integer, primary_key=True)
    disease = db.Column(db.String(255), nullable=False)
    prevalence = db.Column(db.Float, nullable=False)
    sensitivity = db.Column(db.Float, nullable=False)
    false_positive = db.Column(db.Float, nullable=False)
