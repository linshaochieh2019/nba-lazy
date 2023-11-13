from flask import jsonify
from flask_smorest import Blueprint, abort

from db import db
from models import ArticleModel, ArticleSummaryModel

from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError


blp = Blueprint("articles", __name__, description="Article operations")

@blp.route("/articles")
def get_articles():

    today = datetime.utcnow().date()
    articles = ArticleModel.query.filter(
        # db.func.date(ArticleModel.created_at) == today,
        ArticleModel.is_processed == True,
    ).all()

    articles_data = [{
        'id': article.id,
        'chinese_title': article.chinese_title,
        'source': article.source,
        'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'upvotes': article.upvotes
    } for article in articles]

    return jsonify({'articles': articles_data})


@blp.route("/articles/<string:article_id>")
def get_article(article_id):
    article = ArticleModel.query.get_or_404(article_id)
    summary = ArticleSummaryModel.query.filter_by(article_id=article_id).first()

    article_info = {
        'chinese_title': article.chinese_title,
        'source': article.source,
        'URL': article.url,
        'chinese_summary': summary.chinese_summary,
        'created_at': article.created_at.strftime('%Y-%m-%d %H:%M:%S'),  # Format datetime
        'upvotes': article.upvotes,
    }

    return jsonify(article_info)

@blp.route('/articles/<int:article_id>/upvote', methods=['POST'])
def upvote_article(article_id):
    article = ArticleModel.query.get_or_404(article_id)
    article.upvotes += 1
    db.session.commit()
    return jsonify({'upvotes': article.upvotes})
