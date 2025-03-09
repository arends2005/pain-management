from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, BooleanField, PasswordField, SubmitField, SelectField, DateField, URLField, TelField
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional, URL, Regexp
from app.models.user import User

class UserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(3, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots, or underscores')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = TelField('Phone Number', validators=[
        DataRequired(),
        Regexp('^[0-9+\- ]+$', 0, 'Phone number can only contain numbers, +, -, and spaces')
    ])
    password = PasswordField('Password (leave blank to keep unchanged)', validators=[Optional(), Length(min=8)])
    password2 = PasswordField('Confirm Password', validators=[
        EqualTo('password', message='Passwords must match')
    ])
    is_admin = BooleanField('Admin User')
    submit = SubmitField('Update User')

class CreateUserForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), 
        Length(3, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_.]*$', 0, 'Usernames must have only letters, numbers, dots, or underscores')
    ])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone_number = TelField('Phone Number', validators=[
        DataRequired(),
        Regexp('^[0-9+\- ]+$', 0, 'Phone number can only contain numbers, +, -, and spaces')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    is_admin = BooleanField('Admin User')
    submit = SubmitField('Create User')

class SystemSettingsForm(FlaskForm):
    discord_invite_url = URLField('Discord Bot Invite URL', validators=[
        DataRequired(),
        URL(message='Please enter a valid URL')
    ])
    submit = SubmitField('Save Settings')
    
# Add any other admin forms below... 