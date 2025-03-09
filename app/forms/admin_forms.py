from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TelField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo, Optional
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