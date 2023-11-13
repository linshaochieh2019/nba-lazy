import uuid
import requests
from flask import jsonify
from flask_smorest import Blueprint, abort

from db import db
from models import ArticleModel, ParagraphModel

from bs4 import BeautifulSoup
from sqlalchemy.exc import SQLAlchemyError

from utils.text_utils import paragraph_is_lengthy
from utils.article_scraper_utils import get_articles_info

blp = Blueprint("article_scraper", __name__, description="Article scrapping operations")

@blp.route("/get-articles-info", methods=['POST'])
def get_articles_info():
    article_indices = get_articles_info()
    return jsonify({"message": f"Articles successfully stored: {article_indices}"}), 201


@blp.route("/articles/<string:article_id>/scrape", methods=['POST'])
def scrape_paragraphs(article_id):

    # Check if article is already scrapped
    existing_paragraph = ParagraphModel.query.filter_by(article_id=article_id).first()
    if existing_paragraph:
        return jsonify({"message": f"Article id {article_id} is already scraped and stored in db."})

    # The desired URL to scrape
    article = ArticleModel.query.get_or_404(article_id)
    url = article.url

    # Send a GET request to the URL
    response = requests.get(url)

    # Check if the request was successful
    counter = 0
    if response.status_code == 200:
        # Use BeautifulSoup to parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')

        # Loop paragraphs and store in db
        for paragraph in paragraphs:
            if paragraph_is_lengthy(paragraph):
                new_paragraph = ParagraphModel(content=paragraph.text, article_id=article_id)

                # Add instance to the session
                db.session.add(new_paragraph)
                counter += 1

        # Commit the session to the database
        db.session.commit()

        return jsonify({"message": f"Number of paragraphs successfully stored: {counter}"}), 201

    else:
        print(f"Failed to retrieve the web page. Status code: {response.status_code}")
