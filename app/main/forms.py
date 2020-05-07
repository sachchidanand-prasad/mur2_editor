from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, HiddenField
from wtforms.validators import DataRequired, NumberRange

from app.models import User


# editong the profile
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length     
# fix a bug with duplicated usernames
#   doc: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-vii-error-handling
class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])
    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')
                
                

# search form 
# doc: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xvi-full-text-search
from flask import request
class SearchForm(FlaskForm):
    q = StringField('Search', validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        if 'formdata' not in kwargs:
            kwargs['formdata'] = request.args
        if 'csrf_enabled' not in kwargs:
            kwargs['csrf_enabled'] = False
        super(SearchForm, self).__init__(*args, **kwargs)   
        

# Form for upload file
from flask_uploads import UploadSet, IMAGES
from flask_wtf.file import FileField,  FileAllowed, FileRequired
photos = UploadSet('photos', IMAGES)
from flask_wtf import FlaskForm
from wtforms import SubmitField
class UploadForm(FlaskForm):
    photo = FileField(validators=[FileAllowed(photos, 'Image only!'), FileRequired('File was empty!')])
    submit = SubmitField('Upload')    