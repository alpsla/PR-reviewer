from database import db
from datetime import datetime

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pr_url = db.Column(db.String(500), nullable=False)
    review_content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_mock = db.Column(db.Boolean, default=False)
    mock_reason = db.Column(db.String(200))
    github_comment_id = db.Column(db.String(100))
    structured = db.Column(db.Boolean, default=True)
    
    def __init__(self, pr_url, review_content, is_mock=False, mock_reason=None, structured=True):
        self.pr_url = pr_url
        self.review_content = review_content
        self.is_mock = is_mock
        self.mock_reason = mock_reason
        self.structured = structured
    
    def to_dict(self):
        return {
            'id': self.id,
            'pr_url': self.pr_url,
            'review_content': self.review_content,
            'created_at': self.created_at.isoformat(),
            'is_mock': self.is_mock,
            'mock_reason': self.mock_reason,
            'github_comment_id': self.github_comment_id,
            'structured': self.structured
        }
