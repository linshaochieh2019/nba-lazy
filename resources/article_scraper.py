from flask import jsonify
from flask_smorest import Blueprint, abort
from celery import current_app
from tasks import get_articles_info_celery, scrape_paragraphs_celery

blp = Blueprint("article_scraper", __name__, description="Article scrapping operations")

@blp.route("/get-articles-info", methods=['POST'])
def get_articles_info():
    task = current_app.send_task('tasks.get_articles_info_celery')
    response = {"message": "Get articles info task initiated.", "task_id": task.id}
    return jsonify(response), 202

@blp.route("/scrape_paragraphs", methods=['POST'])
def scrape_paragraphs():
    task = current_app.send_task('tasks.scrape_paragraphs_celery')
    response = {"message": "Scraping paragraphs task initiated.", "task_id": task.id}
    return jsonify(response), 202  

