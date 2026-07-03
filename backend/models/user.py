from flask_login import UserMixin
from backend import db
from backend.services.encryption_service import get_encryption_service

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(60), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(160), nullable=True)
    emergency_name = db.Column(db.String(80), nullable=True)
    emergency_relation = db.Column(db.String(50), nullable=True)
    emergency_phone = db.Column(db.String(20), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    height = db.Column(db.Float, nullable=True)
    weight = db.Column(db.Float, nullable=True)
    bmi = db.Column(db.Float, nullable=True)
    _allergies_encrypted = db.Column(db.Text, nullable=True, name="allergies")
    _medical_notes_encrypted = db.Column(db.Text, nullable=True, name="medical_notes")

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"
    
    @property
    def allergies(self):
        if not self._allergies_encrypted:
            return None
        try:
            return get_encryption_service().decrypt(self._allergies_encrypted)
        except Exception:
            return None
    
    @allergies.setter
    def allergies(self, value):
        if value is None:
            self._allergies_encrypted = None
        else:
            self._allergies_encrypted = get_encryption_service().encrypt(str(value))
    
    @property
    def medical_notes(self):
        if not self._medical_notes_encrypted:
            return None
        try:
            return get_encryption_service().decrypt(self._medical_notes_encrypted)
        except Exception:
            return None
    
    @medical_notes.setter
    def medical_notes(self, value):
        if value is None:
            self._medical_notes_encrypted = None
        else:
            self._medical_notes_encrypted = get_encryption_service().encrypt(str(value))
