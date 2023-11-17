from flask import jsonify
from flask_smorest import Blueprint, abort
from celery import current_app
from tasks import generate_embeddings_celery

blp = Blueprint('text_processor', __name__, description="Text processing operations")

@blp.route("/generate_embeddings", methods=['POST'])
def generate_embeddings():
    task = current_app.send_task('tasks.generate_embeddings_celery')
    response = {"message": "Generate embeddings task initiated.", "task_id": task.id}
    return jsonify(response), 202  

@blp.route('/process_texts', methods=['POST'])
def process_texts():
    task = current_app.send_task('tasks.process_texts_celery')
    response = {"message": "Process texts task initiated.", "task_id": task.id}
    return jsonify(response), 202  