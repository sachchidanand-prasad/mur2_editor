"""
This file is defining the object in the DB 
version: 1.0.0
"""

from datetime import datetime
from app import db
from flask_login import UserMixin

# import login from the __init__.py
from app import login
# tracking who is the user
@login.user_loader
def load_user(id):
    return User.query.get(int(id))

from app.search import add_to_index, remove_from_index, query_index
class SearchableMixin(object):
    @classmethod
    def search(cls, expression, page, per_page):
        ids, total = query_index(cls.__tablename__, expression, page, per_page)
        if total == 0:
            return cls.query.filter_by(id=0), 0
        when = []
        for i in range(len(ids)):
            when.append((ids[i], i))
        return cls.query.filter(cls.id.in_(ids)).order_by(
            db.case(when, value=cls.id)), total

    @classmethod
    def before_commit(cls, session):
        session._changes = {
            'add': list(session.new),
            'update': list(session.dirty),
            'delete': list(session.deleted)
        }

    @classmethod
    def after_commit(cls, session):
        for obj in session._changes['add']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['update']:
            if isinstance(obj, SearchableMixin):
                add_to_index(obj.__tablename__, obj)
        for obj in session._changes['delete']:
            if isinstance(obj, SearchableMixin):
                remove_from_index(obj.__tablename__, obj)
        session._changes = None

    @classmethod
    def reindex(cls):
        for obj in cls.query:
            add_to_index(cls.__tablename__, obj)


db.event.listen(db.session, 'before_commit', SearchableMixin.before_commit)
db.event.listen(db.session, 'after_commit', SearchableMixin.after_commit)

# class for pagination of the DB object
class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
            '_links': {
                'self': url_for(endpoint, page=page, per_page=per_page,
                                **kwargs),
                'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                **kwargs) if resources.has_next else None,
                'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                **kwargs) if resources.has_prev else None
            }
        }
        return data


"""
The users on the system
"""
from sqlalchemy.ext.associationproxy import association_proxy


from werkzeug.security import generate_password_hash, check_password_hash
# for reset password email
from time import time
import jwt
# for avarot
from hashlib import md5
class User(UserMixin, PaginatedAPIMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    familyName = db.Column(db.String(64), index=False)
    personalName = db.Column(db.String(64), index=False)
    # email need to be uniq 
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    # the Articles which the User is created, it is basically a SELECT statement on the Article objects
    # articles = db.relationship('Article', secondary=writerrelationship, backref=db.backref('writerrelationship', lazy='dynamic'))
    articles = association_proxy('writerrelationship', 'article')
    
    # some personal info
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return '<User {}>'.format(self.username)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)
    
    # set avator
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(
            digest, size)

# images for the users
class Images(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    addresss = db.Column(db.String(40), index=False)
    
    def __repr__(self):
        return '<Image {}>'.format(self.addresss)
    
# linkt the Article and Writers table together across a third table
#   doc: https://docs.sqlalchemy.org/en/13/orm/extensions/associationproxy.html
#        https://docs.sqlalchemy.org/en/13/orm/basic_relationships.html#many-to-many
#        https://docs.sqlalchemy.org/en/13/orm/basic_relationships.html#Association%20Object
class WriterRelationship(db.Model):
    __tablename__ = 'writerrelationship'
    id = db.Column(db.Integer, primary_key=True)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'))
    # where point the Neo4j relationship, the Neo4j id
    writer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    
    # bidirectional attribute/collection of "user"/"writerrelationship"
    user = db.relationship(User,
                backref=db.backref("writerrelationship",
                                cascade="all, delete-orphan")
            )

    # reference to the "Article" object
    article = db.relationship("Article")     
        
        
"""
The articles on the system
   This is the main object as an Article have got relationship so this need to give the foreign key for the other objects
"""
class Article(SearchableMixin, db.Model):
    __tablename__ = 'article'
    id = db.Column(db.Integer, primary_key=True)    
    title = db.Column(db.String(500), index=True)
    # article language
    language = db.Column(db.String(6))
    # article abstract
    abstract = db.Column(db.String(500))
    # the original markdown text
    markdown = db.Column(db.String(500))
    # the generated html 
    html = db.Column(db.String(140))
    # article status
    status = db.Column(db.String(20))
    # timestamp
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # Wordpresscom id of the post after publishing
    wpcom_id = db.Column(db.Integer, index=False)
    # Wordpresscom address where the things was published
    wpcom_address = db.Column(db.String(140), index=False)

    # make searchable with Elasticsearch the markdown
    __searchable__ = ['markdown']
    
    def __repr__(self):
        return '<Article {}>'.format(self.html)

    