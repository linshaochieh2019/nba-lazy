
from flask import jsonify
from flask_smorest import Blueprint, abort
from celery.result import AsyncResult

blp = Blueprint("tasks", __name__, description="Task operations")

@blp.route("/get_task_result/<string:task_id>", methods=['GET'])
def get_task_result(task_id):
    task_result = AsyncResult(task_id)
    if task_result.successful():
        return jsonify({"message": "Task completed successfully."})
    else:
        return jsonify({"message": "Task is still running or encountered an error."})