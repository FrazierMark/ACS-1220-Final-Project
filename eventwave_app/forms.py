from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, SubmitField
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from eventwave_app.models import User
from eventwave_app.extensions import db
from wtforms.validators import DataRequired, Length, URL, InputRequired
from wtforms import PasswordField
from wtforms.validators import ValidationError
from flask_bcrypt import bcrypt

# class GroceryStoreForm(FlaskForm):
#     """Form for adding/updating a GroceryStore."""
#     title = StringField('Title', validators=[DataRequired(), Length(min=5, max=80, message='Must be between 5 and 180 characters.')])
#     address = StringField('Address', validators=[DataRequired(), Length(min=5, max=200, message='Must be between 5 and 180 characters.')])
#     submit = SubmitField('Submit')
    

# class GroceryItemForm(FlaskForm):
#     """Form for adding/updating a GroceryItem."""
#     name = StringField('Name', validators=[DataRequired(), Length(min=5, max=80, message='Must be between 5 and 180 characters.')])
#     price = StringField('Price', validators=[DataRequired()])
#     category = SelectField('Category', choices=ItemCategory.choices(), validators=[InputRequired('A category is required!'), Length(min=3, max=180, message='Must be between 5 and 180 characters.')])
#     photo_url = StringField('Photo_url', validators=[InputRequired('A photo URL is required!'), URL('Please enter a valid URL.')])
#     store = QuerySelectField('Store', query_factory=lambda: GroceryStore.query, allow_blank=False, get_label='title', validators=[InputRequired('A store is required!')])
#     submit = SubmitField('Submit')
    
class SignUpForm(FlaskForm):
    username = StringField('User Name',
        validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')
        
class LoginForm(FlaskForm):
    username = StringField('User Name',
        validators=[DataRequired(), Length(min=3, max=50)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if not user:
            raise ValidationError('No user with that username. Please try again.')

    def validate_password(self, password):
        user = User.query.filter_by(username=self.username.data).first()
        if user and not bcrypt.checkpw(
                password.data.encode('utf-8'), user.password.encode('utf-8')):
            raise ValidationError('Password doesn\'t match. Please try again.') 