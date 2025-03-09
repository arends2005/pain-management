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
    frequency = SelectField('Frequency', validators=[DataRequired()],
                          choices=[
                              ('every_1_hour', 'Every 1 Hour'),
                              ('every_2_hours', 'Every 2 Hours'),
                              ('every_4_hours', 'Every 4 Hours'),
                              ('every_6_hours', 'Every 6 Hours'),
                              ('every_8_hours', 'Every 8 Hours'),
                              ('every_12_hours', 'Every 12 Hours'),
                              ('once_daily', 'Once Daily'),
                              ('twice_daily', 'Twice Daily'),
                              ('three_times_daily', 'Three Times Daily'),
                              ('four_times_daily', 'Four Times Daily'),
                              ('as_needed', 'As Needed (PRN)'),
                              ('weekly', 'Weekly'),
                              ('biweekly', 'Twice Weekly'),
                              ('monthly', 'Monthly'),
                              ('other', 'Other (See Instructions)')
                          ])
    instructions = TextAreaField('Instructions', validators=[Optional(), Length(0, 500)])
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today)
    end_date = DateField('End Date (Optional)', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Medication')

class ExerciseForm(FlaskForm):
    name = StringField('Exercise Name', validators=[DataRequired(), Length(1, 100)])
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    frequency = SelectField('Frequency', validators=[DataRequired()],
                          choices=[
                              ('daily', 'Daily'),
                              ('twice_daily', 'Twice Daily'),
                              ('three_times_daily', 'Three Times Daily'),
                              ('every_other_day', 'Every Other Day'),
                              ('weekly', 'Weekly'),
                              ('twice_weekly', 'Twice Weekly'),
                              ('three_times_weekly', 'Three Times Weekly'),
                              ('as_needed', 'As Needed'),
                              ('other', 'Other (See Instructions)')
                          ])
    duration = StringField('Duration', validators=[Optional(), Length(0, 50)])
    repetitions = StringField('Repetitions', validators=[Optional(), Length(0, 50)])
    instructions = TextAreaField('Instructions', validators=[Optional(), Length(0, 500)])
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today)
    end_date = DateField('End Date (Optional)', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Exercise')

class TextPreferenceForm(FlaskForm):
    phone_number = TelField('Phone Number', validators=[
        DataRequired(),
        Regexp(r'^\+?[0-9\-\s()]+$', 0, 'Phone number can only contain numbers, +, -, spaces, and parentheses')
    ])
    receive_reminders = BooleanField('Receive Text Reminders', default=True)
    reminder_time = TimeField('Daily Reminder Time', validators=[Optional()])
    reminder_frequency = SelectField('Reminder Frequency', validators=[DataRequired()],
                          choices=[
                              ('hourly_1', 'Every 1 Hour'),
                              ('hourly_2', 'Every 2 Hours'),
                              ('hourly_4', 'Every 4 Hours'),
                              ('hourly_6', 'Every 6 Hours'),
                              ('hourly_8', 'Every 8 Hours'),
                              ('daily', 'Daily'),
                              ('twice_daily', 'Twice Daily'),
                              ('every_other_day', 'Every Other Day'),
                              ('weekly', 'Weekly')
                          ], default='daily')
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