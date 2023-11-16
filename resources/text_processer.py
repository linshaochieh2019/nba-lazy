import os
from flask import request, jsonify, current_app
from flask_smorest import Blueprint, abort
from openai import OpenAI
import pinecone

from models import ArticleModel, ParagraphModel, ArticleSummaryModel
from db import db


# Initialize your Blueprint
blp = Blueprint('text_processor', __name__, description="Text processing operations")


@blp.route('/articles/<string:article_id>/process', methods=['GET'])
def process_text(article_id):

    # Set your OpenAI API key
    client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])

    # Extract the paragraphs from the request
    article = ArticleModel.query.get_or_404(article_id)
    if article.is_processed:
        return jsonify({'message': 'The article is already processed.'})

    paragraphs = ParagraphModel.query.filter_by(article_id=article_id).all()

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
        article_id=article_id,
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

    return jsonify({
        'title': article.title,
        'chinese_title': article.chinese_title,
        'english_summary': article_summary.english_summary,
        'chinese_summary': article_summary.chinese_summary
    })

@blp.route('/articles/generate-embeddings', methods=['POST'])
def generate_embeddings():

    # Extract the paragraphs from the request
    articles = ArticleModel.query.filter_by(has_embedding=False).limit(5).all()
    print(articles, flush=True)
    
    article_texts = {}
    for article in articles:
        paragraphs = ParagraphModel.query.filter_by(article_id=article.id).all()
        text_block = "\n".join([paragraph.content for paragraph in paragraphs])
        article_texts[article.id] = text_block

    # Generate embeddings
    inputs = [v for v in article_texts.values()]

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

    return jsonify({'message': "Vectors upserted."})



