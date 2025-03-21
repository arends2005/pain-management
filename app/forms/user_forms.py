from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, TextAreaField, SelectField, DateField, TimeField,
                    IntegerField, SubmitField, BooleanField, SelectMultipleField, TelField)
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional, Regexp
from datetime import date

class ProfileForm(FlaskForm):
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
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Images only! Allowed formats: JPG, JPEG, PNG, GIF')
    ])
    submit = SubmitField('Update Profile')

class InjuryForm(FlaskForm):
    name = StringField('Injury Name', validators=[DataRequired(), Length(1, 100)])
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    severity = SelectField('Severity', validators=[DataRequired()],
                         choices=[('Mild', 'Mild'), ('Moderate', 'Moderate'), ('Severe', 'Severe')])
    injury_type = SelectField('Type', validators=[DataRequired()],
                            choices=[('Acute', 'Acute'), ('Chronic', 'Chronic')])
    body_location = StringField('Body Location', validators=[DataRequired(), Length(1, 50)])
    date_of_injury = DateField('Date of Injury', validators=[DataRequired()], default=date.today)
    submit = SubmitField('Save Injury')

class ProgressLogForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], default=date.today)
    pain_level = IntegerField('Pain Level (1-10)', validators=[
        DataRequired(),
        NumberRange(min=1, max=10, message='Please enter a value between 1 and 10')
    ])
    mobility = IntegerField('Mobility Percentage (0-100)', validators=[
        Optional(),
        NumberRange(min=0, max=100, message='Please enter a value between 0 and 100')
    ])
    notes = TextAreaField('Notes', validators=[Optional(), Length(0, 500)])
    submit = SubmitField('Save Progress')

class RecoveryPlanForm(FlaskForm):
    name = StringField('Plan Name', validators=[DataRequired(), Length(1, 100)])
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    injury_id = SelectField('Injury', validators=[DataRequired()], coerce=int)
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today)
    end_date = DateField('End Date (Optional)', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Plan')

class MedicationForm(FlaskForm):
    name = StringField('Medication Name', validators=[DataRequired(), Length(1, 100)])
    dosage = StringField('Dosage', validators=[DataRequired(), Length(1, 50)])
    frequency = SelectField('Frequency', validators=[DataRequired()], coerce=int,
                          choices=[
                              (1, 'Every 1 Hour'),
                              (2, 'Every 2 Hours'),
                              (4, 'Every 4 Hours'),
                              (6, 'Every 6 Hours'),
                              (8, 'Every 8 Hours'),
                              (12, 'Every 12 Hours'),
                              (24, 'Every 24 Hours'),
                              (168, 'Weekly'), # 24*7
                              (84, 'Twice Weekly'), # 24*7/2
                              (672, 'Monthly') # 24*28
                          ])
    instructions = TextAreaField('Instructions', validators=[Optional(), Length(0, 500)])
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today)
    end_date = DateField('End Date (Optional)', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    discord_notifications = BooleanField('Enable Discord Notifications', default=False)
    submit = SubmitField('Save Medication')

class ExerciseForm(FlaskForm):
    name = StringField('Exercise Name', validators=[DataRequired(), Length(1, 100)])
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    frequency = SelectField('Frequency', validators=[DataRequired()], coerce=int,
                          choices=[
                              (1, 'Every 1 Hour'),
                              (2, 'Every 2 Hours'),
                              (4, 'Every 4 Hours'),
                              (6, 'Every 6 Hours'),
                              (8, 'Every 8 Hours'),
                              (12, 'Every 12 Hours'),
                              (24, 'Every 24 Hours'),
                              (48, 'Every 2 Days'),
                              (168, 'Weekly'), # 24*7
                              (84, 'Twice Weekly'), # 24*7/2
                              (56, 'Three Times Weekly'), # 24*7/3
                              (672, 'Monthly') # 24*28
                          ])
    duration = StringField('Duration', validators=[Optional(), Length(0, 50)])
    repetitions = StringField('Repetitions', validators=[Optional(), Length(0, 50)])
    instructions = TextAreaField('Instructions', validators=[Optional(), Length(0, 500)])
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today)
    end_date = DateField('End Date (Optional)', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    discord_notifications = BooleanField('Enable Discord Notifications', default=False)
    submit = SubmitField('Save Exercise')

class TextPreferenceForm(FlaskForm):
    phone_number = TelField('Phone Number', validators=[
        DataRequired(),
        Regexp(r'^\+?[0-9\-\s()]+$', 0, 'Phone number can only contain numbers, +, -, spaces, and parentheses')
    ])
    receive_reminders = BooleanField('Receive Text Reminders', default=True)
    reminder_time = TimeField('Daily Reminder Time', validators=[Optional()])
    reminder_frequency = SelectField('Reminder Frequency', validators=[DataRequired()], coerce=int,
                          choices=[
                              (1, 'Every 1 Hour'),
                              (2, 'Every 2 Hours'),
                              (4, 'Every 4 Hours'),
                              (6, 'Every 6 Hours'),
                              (8, 'Every 8 Hours'),
                              (12, 'Every 12 Hours'),
                              (24, 'Every 24 Hours'),
                              (48, 'Every 2 Days'),
                              (168, 'Weekly'), # 24*7
                              (84, 'Twice Weekly'), # 24*7/2
                              (672, 'Monthly') # 24*28
                          ], default=24)
    receive_progress_updates = BooleanField('Receive Progress Updates', default=True)
    enabled = BooleanField('Enable Text Reminders', default=True)
    daily_limit = IntegerField('Maximum Daily Texts', validators=[
        DataRequired(),
        NumberRange(min=1, max=20, message='Please enter a value between 1 and 20')
    ], default=5)
    quiet_hours_start = TimeField('Quiet Hours Start (Optional)', validators=[Optional()])
    quiet_hours_end = TimeField('Quiet Hours End (Optional)', validators=[Optional()])
    time_zone = SelectField('Time Zone', validators=[DataRequired()],
                          choices=[
                              ('UTC', 'UTC'),
                              ('US/Eastern', 'Eastern Time (US)'),
                              ('US/Central', 'Central Time (US)'),
                              ('US/Mountain', 'Mountain Time (US)'),
                              ('US/Pacific', 'Pacific Time (US)')
                          ], default='UTC')
    submit = SubmitField('Save Preferences')

class TwilioTestForm(FlaskForm):
    phone_number = TelField('Phone Number', validators=[
        DataRequired(),
        Regexp('^[0-9+\- ]+$', 0, 'Phone number can only contain numbers, +, -, and spaces')
    ])
    message = TextAreaField('Message', validators=[
        DataRequired(),
        Length(1, 160, message='Message must be between 1 and 160 characters')
    ], default="This is a test message from the Pain Management App.")
    submit = SubmitField('Send Test Message')

class DiscordPreferenceForm(FlaskForm):
    discord_channel_id = StringField('Discord Channel ID', validators=[
        Optional(),
        Regexp(r'^\d{17,19}$', 0, 'Discord Channel ID must be a valid 17-19 digit number')
    ])
    enabled = BooleanField('Enable Discord Reminders', default=True)
    receive_reminders = BooleanField('Receive Discord Reminders', default=True)
    receive_progress_updates = BooleanField('Receive Progress Updates', default=True)
    daily_limit = IntegerField('Maximum Daily Messages', validators=[
        DataRequired(),
        NumberRange(min=1, max=20, message='Please enter a value between 1 and 20')
    ], default=5)
    quiet_hours_start = TimeField('Quiet Hours Start (Optional)', validators=[Optional()])
    quiet_hours_end = TimeField('Quiet Hours End (Optional)', validators=[Optional()])
    time_zone = SelectField('Time Zone', validators=[DataRequired()],
                          choices=[
                              ('UTC', 'UTC'),
                              ('US/Eastern', 'Eastern Time (US)'),
                              ('US/Central', 'Central Time (US)'),
                              ('US/Mountain', 'Mountain Time (US)'),
                              ('US/Pacific', 'Pacific Time (US)')
                          ], default='UTC')
    submit = SubmitField('Save Preferences') 