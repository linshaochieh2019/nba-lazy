import requests
from models import ArticleModel
from db import db
from flask import jsonify

def get_articles_info():

    print('Running scraper task ...', flush=True)

    url = "https://nba-latest-news.p.rapidapi.com/articles?limit=10"

    headers = {
        "X-RapidAPI-Key": "fa34c6da67msh38fe0d80dadf5d1p15a2b0jsne6bed5dbfce5",
        "X-RapidAPI-Host": "nba-latest-news.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    articles_data = response.json()

    # Iterate through each article in the response
    article_indices = []
    for e_id, article_info in enumerate(articles_data):
        print(e_id, flush=True)
        
        # Check if article exists in db
        existing_article = ArticleModel.query.filter_by(
            url = article_info['url']
        ).first()
        if existing_article:
            continue

        # Create an instance of ArticleModel
        article = ArticleModel(
            title=article_info['title'],
            source=article_info['source'],
            url=article_info['url']
        )

        # Add instance to the session
        db.session.add(article)
        article_indices.append(article.id)

    # Commit the session to the database
    db.session.commit()
    return jsonify({'message': f'Articles info stored: {article_indices}'})