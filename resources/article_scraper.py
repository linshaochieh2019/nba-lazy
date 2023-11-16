import uuid
import requests
from flask import jsonify
from flask_smorest import Blueprint, abort

from db import db
from models import ArticleModel, ParagraphModel

from bs4 import BeautifulSoup
from sqlalchemy.exc import SQLAlchemyError

from utils import paragraph_is_lengthy
from celery import current_app

blp = Blueprint("article_scraper", __name__, description="Article scrapping operations")

@blp.route("/get-articles-info", methods=['POST'])
def get_articles_info():
    task = current_app.send_task('tasks.get_articles_info_celery')
    return jsonify({"message": "Articles successfully stored."}), 201

@blp.route("/scrape_paragraphs", methods=['POST'])
def scrape_paragraphs():
    task = current_app.send_task('tasks.scrape_paragraphs_celery')
    return jsonify({"message": f"Paragraphs successfully stored."}), 201
