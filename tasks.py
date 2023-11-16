import requests
from models import ArticleModel, ParagraphModel
from bs4 import BeautifulSoup
from db import db
from flask import jsonify

from celery import shared_task
from utils import paragraph_is_lengthy

@shared_task(bind=True)
def get_articles_info_celery(self):

    print('Running task with Celery: getting articles info ...', flush=True)

    url = "https://nba-latest-news.p.rapidapi.com/articles?limit=10"

    headers = {
        "X-RapidAPI-Key": "fa34c6da67msh38fe0d80dadf5d1p15a2b0jsne6bed5dbfce5",
        "X-RapidAPI-Host": "nba-latest-news.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    articles_data = response.json()

    # Iterate through each article in the response
    for e_id, article_info in enumerate(articles_data):
        print(e_id, flush=True)
        
        # Check if article exists in db
        existing_article = ArticleModel.query.filter_by(
            url = article_info['url']
        ).first()
        if existing_article:
            print(f'Article id {existing_article.id} already scraped.', flush=True)
            continue

        # Create an instance of ArticleModel
        article = ArticleModel(
            title=article_info['title'],
            source=article_info['source'],
            url=article_info['url']
        )

        # Add instance to the session
        db.session.add(article)

    # Commit the session to the database
    db.session.commit()


@shared_task(bind=True)
def scrape_paragraphs_celery(self):

    article_id = 60
    print('Running task with Celery: Scraping paragraphs ...', flush=True)

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