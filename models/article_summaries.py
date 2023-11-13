from db import db
from datetime import datetime

class ArticleSummaryModel(db.Model):
    __tablename__ = 'article_summaries'

    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    english_summary = db.Column(db.Text)
    chinese_summary = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    article = db.relationship('ArticleModel', back_populates='summaries')
