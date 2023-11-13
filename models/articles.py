from db import db
from datetime import datetime

class ArticleModel(db.Model):
    __tablename__ = 'articles'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    chinese_title = db.Column(db.String(255))
    source = db.Column(db.String(255))
    url = db.Column(db.String(512))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    paragraphs = db.relationship('ParagraphModel', back_populates='article')
    summaries = db.relationship('ArticleSummaryModel', back_populates='article')
    is_processed = db.Column(db.Boolean, default=False)
    has_embedding = db.Column(db.Boolean, default=False)
    upvotes = db.Column(db.Integer, default=0)



