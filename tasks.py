import os
import requests
from models import ArticleModel, ParagraphModel, ArticleSummaryModel
from bs4 import BeautifulSoup
from db import db
from flask import jsonify, current_app

from celery import shared_task
from utils import paragraph_is_lengthy

from openai import OpenAI
import pinecone

import logging
logging.basicConfig(level=logging.INFO)

@shared_task(bind=True)
def get_articles_info_celery(self):
    logger = logging.getLogger(__name__)
    logger.info('Running task with Celery: getting articles info ...')

    url = "https://nba-latest-news.p.rapidapi.com/articles?limit=10"

    headers = {
        "X-RapidAPI-Key": "fa34c6da67msh38fe0d80dadf5d1p15a2b0jsne6bed5dbfce5",
        "X-RapidAPI-Host": "nba-latest-news.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)
    articles_data = response.json()

    # Iterate through each article in the response
    for article_info in articles_data:        
        # Check if article exists in db
        existing_article = ArticleModel.query.filter_by(
            url = article_info['url']
        ).first()
        if existing_article:
            logger.info(f'Article id {existing_article.id} already scraped.')
            continue

        # Create an instance of ArticleModel
        article = ArticleModel(
            title=article_info['title'],
            source=article_info['source'],
            url=article_info['url'],
            has_paragraphs=False
        )

        # Add instance to the session
        db.session.add(article)

    # Commit the session to the database
    db.session.commit()
    logger.info('Task completed successfully.')


@shared_task(bind=True)
def scrape_paragraphs_celery(self):
    logger = logging.getLogger(__name__)
    logger.info('Running task with Celery: Scraping paragraphs ...')

    # Retrieve articles that don't have paragraphs yet
    articles = ArticleModel.query.filter_by(has_paragraphs=False).all()
    logger.info(f"Scraping paragraphs for {len(articles)} articles.")

    # The desired URL to scrape
    for article in articles:
        url = article.url

        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            # Use BeautifulSoup to parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            paragraphs = soup.find_all('p')

            # Loop paragraphs and store in db
            for paragraph in paragraphs:
                if paragraph_is_lengthy(paragraph):
                    new_paragraph = ParagraphModel(content=paragraph.text, article_id=article.id)

                    # Add instance to the session
                    db.session.add(new_paragraph)

                    # Update article log
                    article.has_paragraphs = True

    # Commit the session to the database
    db.session.commit()
    logger.info('Task completed successfully.')

@shared_task(bind=True)
def generate_embeddings_celery(self):
    logger = logging.getLogger(__name__)
    logger.info('Running task with Celery: Generating embeddings ...')

    articles = ArticleModel.query.filter_by(has_embedding=False).all()
    logger.info(f'Generating embeddings for {len(articles)} articles.')

    article_texts = {}
    for article in articles:
        paragraphs = ParagraphModel.query.filter_by(article_id=article.id).all()
        text_block = "\n".join([paragraph.content for paragraph in paragraphs])
        article_texts[article.id] = text_block

    # Generate embeddings
    inputs = [v for v in article_texts.values()]

    # Connecting to OpenAI API
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=inputs,
        encoding_format="float"
        )

    # Reformat to vectors
    vectors = [{'id': str(article_id), 'values': embedding.embedding} 
                for article_id, embedding in zip(article_texts.keys(), response.data)]
    
    # Connect to pincone index and upsert vectors
    pinecone.init(      
        api_key=os.getenv('PINECONE_API_KEY'),
        environment='us-west1-gcp'      
    )      
    index = pinecone.Index('nba-lazy')
    index.upsert(vectors=vectors)

    # Flag articles as has_embedding
    for article in articles:
        article.has_embedding = True
    db.session.commit()
    logger.info('Task completed successfully.')

@shared_task(bind=True)
def process_texts_celery(self):
    logger = logging.getLogger(__name__)
    logger.info('Running task with Celery: Process texts ...')

    articles = ArticleModel.query.filter_by(is_processed=False).limit(5).all()
    logger.info(f'Text processing for {len(articles)} articles.')

    # Set your OpenAI API key
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])

    for article in articles:
        paragraphs = ParagraphModel.query.filter_by(article_id=article.id).all()

        # Concatenate paragraphs into a single text block
        text_block = "\n".join([paragraph.content for paragraph in paragraphs])

        # Step 1: Generate summary in English
        summary_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sport journalist assistant, skilled in summarizing long text about NBA stories."},
                {"role": "user", "content": f"Summarize the following text in detail: {text_block}"}
            ],
            max_tokens=1024,  # Increase max_tokens as needed
            temperature=0.7,  # Adjust as needed
        )
        english_summary = summary_response.choices[0].message.content

        # Step 2: Translate the summary into Traditional Chinese with Taiwanese wording
        translation_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sport journalist assistant, skilled in translating NBA stories into Traditional Chinese (Taiwanese wording)."},
                {"role": "user", "content": f"Translate the following text: {english_summary}"}
            ],
            max_tokens=1024,  # Increase max_tokens as needed
            temperature=0.7,  # Adjust as needed
        )
        chinese_summary = translation_response.choices[0].message.content

        # Store an article summary instance
        article_summary = ArticleSummaryModel(
            article_id=article.id,
            english_summary=english_summary,
            chinese_summary=chinese_summary,
        )
        db.session.add(article_summary)

        # Step 3: Translate title into Traditional Chinese with Taiwanese wording
        title_translation_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a sport journalist assistant, skilled in translating NBA stories into Traditional Chinese (Taiwanese wording)."},
                {"role": "user", "content": f"Translate the following article title: {article.title}"}
            ],
            max_tokens=60,  # Increase max_tokens as needed
            temperature=0.7,  # Adjust as needed
        )
        chinese_title = title_translation_response.choices[0].message.content
        article.chinese_title = chinese_title
        article.is_processed = True

    db.session.commit()
    logger.info('Task completed successfully.')
