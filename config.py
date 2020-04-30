import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    # own address do not put / on the end !!!
    SELF_ADDRESS = 'http://mur2.co.uk'
    # secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    # DB settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # how many article on one page
    ARTICLE_PER_PAGE = 25
    # full text search engine
    ELASTICSEARCH_URL = 'http://localhost:9200'
    # login details for Neo4j creating user
    CREATUSER = "createuser"
    CREATUSER_PASSWORD = "abcxyz"
    RESTAPI_USER = "user1"
    RESTAPI_PASSWORD = "abcxyz"
    MUR2_REST_ADDRESS = ""
    # email
    MAIL_SERVER = ''
    MAIL_PORT = 465
    MAIL_USE_TLS = True
    MAIL_USERNAME = ''
    MAIL_PASSWORD = ''
    ADMINS = ['']
    # supported languages
    LANGUAGES = ['en', 'hu', 'es', 'zh', 'ru' ]
    # wordpress.com app settings
    APP_WORDPRESSCOM_ID = ''
    APP_WORDPRESSCOM_PASSWORD = ''
    # upload for users
    UPLOAD_FOLDER = "/Frontend/users_data"
    UPLOADED_PHOTOS_DEST = "/Frontend/users_data"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
