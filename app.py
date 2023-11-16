import os

from flask import Flask
from flask_smorest import Api
from flask_migrate import Migrate
from flask_cors import CORS

from resources.article_scraper import blp as ArticleScraperBlueprint
from resources.text_processer import blp as TextProcesserBlueprint
from resources.articles import blp as ArticleBlueprint

from models import ArticleModel
from dotenv import load_dotenv
from db import db

from tasks import get_articles_info_celery

from celery import Celery

def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config["CELERY_CONFIG"])

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

def create_app():
    app = Flask(__name__)
    load_dotenv()

    # App configurations
    app.config["PROPAGATE_EXCEPTIONS"] = True
    app.config["API_TITLE"] = "TTT REST API"
    app.config["API_VERSION"] = "v1"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    app.config["OPENAPI_URL_PREFIX"] = "/"
    app.config["OPENAPI_SWAGGER_UI_PATH"] = "/swagger-ui"
    app.config["OPENAPI_SWAGGER_UI_URL"] = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"

    # Secret key
    # app.config["SECRET_KEY"] = "Oz8Z7Iu&DwoQK)g%*Wit2YpE#-46vy0n"

    # DB configurations
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    migrate = Migrate(app, db)

    # Registrations
    api = Api(app)
    api.register_blueprint(ArticleScraperBlueprint)
    api.register_blueprint(TextProcesserBlueprint)
    api.register_blueprint(ArticleBlueprint)

    # CORS configurations
    allowed_origins = [
        "http://localhost:3000",
    ]

    # Configure CORS to allow multiple origins
    CORS(app, resources={r"/*": {"origins": allowed_origins}})

    # # OpenAI configuration
    # app.config['OPENAI_API_KEY'] = os.getenv("OPENAI_API_KEY")

    # Celery configurations
    app.config["CELERY_CONFIG"] = {"broker_url": "redis://redis", "result_backend": "redis://redis"}
    celery = make_celery(app)
    celery.set_default()

    return app, celery
