from flask import Flask, request, current_app
# configuration
from config import Config

import os

# search
from elasticsearch import Elasticsearch

# DB
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()
# DB migration
from flask_migrate import Migrate
migrate = Migrate()
# international
from flask_babel import Babel, lazy_gettext as _l
from flask import request
babel = Babel()
# login
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
from flask_login import LoginManager
login = LoginManager()
login.login_view = 'auth.login'
login.login_message = _l('Please log in to access this page.')
# mail
from flask_mail import Mail
mail = Mail()
# bootstrap
# from flask_bootstrap import Bootstrap
# bootstrap = Bootstrap()
# Moment
# from flask_moment import Moment
# moment = Moment()
# Upload files
from flask_uploads import configure_uploads, patch_request_class
from app.main.forms import photos


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    app.app_context().push()
    db.create_all()
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    # bootstrap.init_app(app)
    # moment.init_app(app)
    babel.init_app(app)    
    
    # search engine
    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) \
        if app.config['ELASTICSEARCH_URL'] else None
    print(app.config['ELASTICSEARCH_URL'])
    print(app.elasticsearch)

    # erros blueprint
    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)
    
    # auth blueplint
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    # the main of the app
    from app.main import bp as main_bp
    app.register_blueprint(main_bp)
        
    if not app.debug and not app.testing:
        if app.config['MAIL_SERVER']:
            auth = None
            if app.config['MAIL_USERNAME'] or app.config['MAIL_PASSWORD']:
                auth = (app.config['MAIL_USERNAME'],
                        app.config['MAIL_PASSWORD'])
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

        # logs
        if not os.path.exists('logs'):
            os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/mur2.log',
                                               maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Mur2 startup')

    # configuration the Flask-upload
    configure_uploads(app, photos)    
        
    return app

# international
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(current_app.config['LANGUAGES'])


from app import models




