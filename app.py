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

from utils.celery_utils import make_celery

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

    # Celery configurations
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0' 
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    celery = make_celery(app)

    return app
