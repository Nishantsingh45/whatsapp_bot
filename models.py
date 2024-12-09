from flask_sqlalchemy import SQLAlchemy
import uuid
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    phone = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String)
    image = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    receipts = db.relationship('Receipt', backref='user', lazy=True)

class Receipt(db.Model):
    __tablename__ = 'receipts'
    id = db.Column(db.String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    image_url = db.Column(db.String, nullable=False)
    date_time = db.Column(db.String)
    amount = db.Column(db.Float)
    seller = db.Column(db.String)
    summary = db.Column(db.String)
    category = db.Column(db.String)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)