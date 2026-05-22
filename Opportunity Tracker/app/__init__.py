from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
import os
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager

import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from shared_models.models import db 

migrate = Migrate()

load_dotenv()

from flask_jwt_extended import JWTManager

def create_app():
    app = Flask(__name__)

    app.config.from_object("config.Config")

    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    
    app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
    
    app.config["JWT_COOKIE_SECURE"] = False  # True in production HTTPS
    app.config["JWT_COOKIE_CSRF_PROTECT"] = False
    
    jwt = JWTManager(app)


    db.init_app(app)
    migrate.init_app(app,db)

    logging.basicConfig(level=logging.INFO)
    from app.admin import admin_bp
    from app.employee import employee_bp
    from app.base import base_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(base_bp)
    return app
