from flask import jsonify, render_template
from flask_smorest import Blueprint, abort

from db import db
from models import ArticleModel, ArticleSummaryModel

blp = Blueprint("articles", __name__, description="Article operations")

@blp.route("/")
def get_articles():

    articles = ArticleModel.query.filter(
        ArticleModel.is_processed == True,
    ).all()

    return render_template('index.html', articles=articles)


@blp.route("/articles/<string:article_id>")
def get_article(article_id):
    article = ArticleModel.query.get_or_404(article_id)
    summary = ArticleSummaryModel.query.filter_by(article_id=article_id).first()

    return render_template('article.html', article=article, summary=summary)

@blp.route('/articles/<int:article_id>/upvote', methods=['POST'])
def upvote_article(article_id):
    article = ArticleModel.query.get_or_404(article_id)
    article.upvotes += 1
    db.session.commit()
    return jsonify({'upvotes': article.upvotes})
