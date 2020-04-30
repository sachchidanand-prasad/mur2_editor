from flask import Flask
# configuration
from config import Config
# DB
from flask_sqlalchemy import SQLAlchemy
# DB migration
from flask_migrate import Migrate
# Mail
from flask_mail import Mail
# international
from flask_babel import Babel
from flask import request


app = Flask(__name__, static_url_path='/static', static_folder ='static')

# config
app.config.from_object(Config)

# login manager
from flask_login import LoginManager
login = LoginManager(app)

# international
babel = Babel(app)
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(app.config['LANGUAGES'])


# DB
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# full text search engine
from elasticsearch import Elasticsearch
app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None

# logging
import logging
from logging.handlers import RotatingFileHandler
import os
if not app.debug:

    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/mur2.log', maxBytes=10240,
                                       backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Mur2 startup')

# Mail
import logging
from logging.handlers import SMTPHandler
if not app.debug:
    if app.config['MAIL_SERVER']:
        auth = None
        if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
            auth = (app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
        secure = None
        if app.config['MAIL_USE_TLS']:
            secure = ()
        mail_handler = SMTPHandler(
            mailhost=(app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
            fromaddr='no-reply@' + app.config['MAIL_SERVER'],
            toaddrs=app.config['ADMINS'], subject='Microblog Failure',
            credentials=auth, secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
        
mail = Mail(app)

# the routes, addresses, etc
from app import routes, models

