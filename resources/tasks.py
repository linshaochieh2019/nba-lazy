
from flask import jsonify
from flask_smorest import Blueprint, abort
from celery.result import AsyncResult

# Debugger
import os
import requests
from models import ArticleModel, ParagraphModel, ArticleSummaryModel
from bs4 import BeautifulSoup
from db import db
from flask import jsonify, current_app
from sqlalchemy import desc


from celery import shared_task
from utils import paragraph_is_lengthy, count_words, extract_words

from openai import OpenAI
import pinecone

import logging
logging.basicConfig(level=logging.INFO)


blp = Blueprint("tasks", __name__, description="Task operations")

@blp.route("/get_task_result/<string:task_id>", methods=['GET'])
def get_task_result(task_id):
    task_result = AsyncResult(task_id)
    if task_result.successful():
        return jsonify({"message": "Task completed successfully."})
    else:
        return jsonify({"message": "Task is still running or encountered an error."})
    
@blp.route("/debugger", methods=['POST'])
def debugger():
    logger = logging.getLogger(__name__)
    logger.info('Running task with Celery: Process texts ...')

    articles = ArticleModel.query.filter_by(
        has_paragraphs=True,
        is_processed=False
        ).all()
    logger.info(f'Text processing for {len(articles)} articles.')

    # Set your OpenAI API key
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])

    for article in articles:
        paragraphs = ParagraphModel.query.filter_by(article_id=article.id).all()
        text_block = "\n".join([paragraph.content for paragraph in paragraphs])

        logger.info(f' -- article id {article.id}')
        if count_words(text_block) > 2000:
            logger.info(' ---- text is longer than 2000 words, therefore getting extract.')
            text_block = extract_words(text_block)

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
                {"role": "user", "content": f"Translate the following text to 繁體中文: {english_summary}"}
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
                {"role": "user", "content": f"Translate the following article title to 繁體中文: {article.title}"}
            ],
            max_tokens=60,  # Increase max_tokens as needed
            temperature=0.7,  # Adjust as needed
        )
        chinese_title = title_translation_response.choices[0].message.content
        article.chinese_title = chinese_title
        article.is_processed = True

        db.session.commit()
    logger.info('Task completed successfully.')
