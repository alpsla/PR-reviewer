from app import db
from datetime import datetime

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pr_url = db.Column(db.String(500), nullable=False)
    review_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
