from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, g
from flask_login import login_required, current_user
from datetime import datetime, date
from app.extensions import db
from app.models.user import User, TextPreference
from app.models.injury import Injury, ProgressLog
from app.models.recovery_plan import RecoveryPlan, Medication, Exercise, MedicationDose, ExerciseSession
from app.forms.user_forms import (InjuryForm, ProgressLogForm, RecoveryPlanForm, 
                                MedicationForm, ExerciseForm, TextPreferenceForm, ProfileForm, TwilioTestForm)
import os
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from app.utils.logging_helper import TwilioLogger
import requests
from werkzeug.utils import secure_filename
import uuid
from app.forms.auth_forms import ChangePasswordForm  # Import here to avoid circular imports

user = Blueprint('user', __name__)

@user.route('/dashboard')
@login_required
def dashboard():
    injuries = Injury.query.filter_by(user_id=current_user.id).all()
    active_recovery_plans = RecoveryPlan.query.filter_by(
        user_id=current_user.id, 
        is_active=True
    ).all()
    
    # Get recent medication doses and exercise sessions
    recent_meds = MedicationDose.query.join(Medication).join(RecoveryPlan).filter(
        RecoveryPlan.user_id == current_user.id
    ).order_by(MedicationDose.timestamp.desc()).limit(5).all()
    
    recent_exercises = ExerciseSession.query.join(Exercise).join(RecoveryPlan).filter(
        RecoveryPlan.user_id == current_user.id
    ).order_by(ExerciseSession.timestamp.desc()).limit(5).all()
    
    return render_template('user/dashboard.html', 
                          injuries=injuries, 
                          recovery_plans=active_recovery_plans,
                          recent_meds=recent_meds,
                          recent_exercises=recent_exercises)

# Injury management
@user.route('/injuries')
@login_required
def injuries():
    injuries = Injury.query.filter_by(user_id=current_user.id).all()
    return render_template('user/injuries/index.html', injuries=injuries)

@user.route('/injuries/new', methods=['GET', 'POST'])
@login_required
def new_injury():
    form = InjuryForm()
    if form.validate_on_submit():
        injury = Injury(
            user_id=current_user.id,
            name=form.name.data,
            description=form.description.data,
            severity=form.severity.data,
            injury_type=form.injury_type.data,
            body_location=form.body_location.data,
            date_of_injury=form.date_of_injury.data
        )
        db.session.add(injury)
        db.session.commit()
        flash('Injury added successfully!', 'success')
        return redirect(url_for('user.injuries'))
    return render_template('user/injuries/new.html', form=form)

@user.route('/injuries/<int:id>')
@login_required
def show_injury(id):
    injury = Injury.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    progress_logs = ProgressLog.query.filter_by(injury_id=injury.id).order_by(ProgressLog.date.desc()).all()
    recovery_plans = RecoveryPlan.query.filter_by(injury_id=injury.id).all()
    return render_template('user/injuries/show.html', 
                          injury=injury, 
                          progress_logs=progress_logs,
                          recovery_plans=recovery_plans)

@user.route('/injuries/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_injury(id):
    injury = Injury.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = InjuryForm(obj=injury)
    
    if form.validate_on_submit():
        form.populate_obj(injury)
        db.session.commit()
        flash('Injury updated successfully!', 'success')
        return redirect(url_for('user.show_injury', id=injury.id))
    
    return render_template('user/injuries/edit.html', form=form, injury=injury)

@user.route('/injuries/<int:id>/log', methods=['GET', 'POST'])
@login_required
def add_progress_log(id):
    injury = Injury.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = ProgressLogForm()
    
    if form.validate_on_submit():
        log = ProgressLog(
            injury_id=injury.id,
            date=form.date.data,
            pain_level=form.pain_level.data,
            notes=form.notes.data,
            mobility=form.mobility.data
        )
        db.session.add(log)
        db.session.commit()
        flash('Progress log added successfully!', 'success')
        return redirect(url_for('user.show_injury', id=injury.id))
    
    # Default to today's date
    form.date.data = date.today()
    return render_template('user/injuries/add_log.html', form=form, injury=injury)

# Recovery Plan management
@user.route('/recovery-plans')
@login_required
def recovery_plans():
    plans = RecoveryPlan.query.filter_by(user_id=current_user.id).all()
    return render_template('user/recovery_plans/index.html', plans=plans)

@user.route('/recovery-plans/new', methods=['GET', 'POST'])
@login_required
def new_recovery_plan():
    form = RecoveryPlanForm()
    form.injury_id.choices = [(i.id, i.name) for i in Injury.query.filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        plan = RecoveryPlan(
            user_id=current_user.id,
            injury_id=form.injury_id.data,
            name=form.name.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=True
        )
        db.session.add(plan)
        db.session.commit()
        flash('Recovery plan created successfully!', 'success')
        return redirect(url_for('user.show_recovery_plan', id=plan.id))
    
    form.start_date.data = date.today()
    return render_template('user/recovery_plans/new.html', form=form)

@user.route('/recovery-plans/<int:id>')
@login_required
def show_recovery_plan(id):
    plan = RecoveryPlan.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    medications = Medication.query.filter_by(recovery_plan_id=plan.id).all()
    exercises = Exercise.query.filter_by(recovery_plan_id=plan.id).all()
    
    return render_template('user/recovery_plans/show.html', 
                          plan=plan,
                          medications=medications,
                          exercises=exercises)

# Text preferences
@user.route('/text-preferences', methods=['GET', 'POST'])
@login_required
def text_preferences():
    text_pref = TextPreference.query.filter_by(user_id=current_user.id).first()
    if not text_pref:
        text_pref = TextPreference(
            user_id=current_user.id, 
            enabled=True,
            phone_number=current_user.phone_number
        )
        db.session.add(text_pref)
        db.session.commit()
    elif not text_pref.phone_number and current_user.phone_number:
        # Set phone number from user if not already set
        text_pref.phone_number = current_user.phone_number
        db.session.commit()
    
    form = TextPreferenceForm(obj=text_pref)
    
    if form.validate_on_submit():
        # Format phone number if provided
        if form.phone_number.data:
            # Remove all non-numeric characters except + (for international numbers)
            import re
            cleaned_number = re.sub(r'[^\d+]', '', form.phone_number.data)
            
            # Format US numbers if they appear to be US format
            if len(cleaned_number) == 10 and not cleaned_number.startswith('+'):
                form.phone_number.data = f"+1{cleaned_number}"
            elif len(cleaned_number) == 11 and cleaned_number.startswith('1') and not cleaned_number.startswith('+'):
                form.phone_number.data = f"+{cleaned_number}"
            else:
                form.phone_number.data = cleaned_number
                
            # Validate it still matches our pattern
            import re
            if not re.match(r'^\+?[0-9]+$', form.phone_number.data):
                flash('Invalid phone number format. Please use digits only with an optional + prefix.', 'danger')
                return render_template('user/text_preferences.html', form=form)
        
        # Populate the object with the form data
        form.populate_obj(text_pref)
        db.session.commit()
        flash('Text preferences updated successfully!', 'success')
        return redirect(url_for('user.dashboard'))
    
    return render_template('user/text_preferences.html', form=form)

# Profile management
@user.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        
        if form.profile_picture.data and hasattr(form.profile_picture.data, 'filename'):
            try:
                # Generate upload paths
                static_dir = os.path.join('app', 'static')
                uploads_dir = os.path.join(static_dir, 'uploads')
                profile_pics_dir = os.path.join(uploads_dir, 'profile_pics')
                
                # Create directories if they don't exist - use absolute paths
                abs_static_dir = os.path.join('/app', static_dir)
                abs_uploads_dir = os.path.join('/app', uploads_dir)
                abs_profile_pics_dir = os.path.join('/app', profile_pics_dir)
                
                # Create each directory in sequence
                if not os.path.exists(abs_static_dir):
                    os.makedirs(abs_static_dir)
                if not os.path.exists(abs_uploads_dir):
                    os.makedirs(abs_uploads_dir)
                if not os.path.exists(abs_profile_pics_dir):
                    os.makedirs(abs_profile_pics_dir)
                
                # Generate a unique filename
                original_filename = secure_filename(form.profile_picture.data.filename)
                file_ext = os.path.splitext(original_filename)[1].lower()
                # Only allow certain extensions
                if file_ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                    flash('Only JPG, JPEG, PNG, and GIF files are allowed!', 'danger')
                else:
                    # Save the file with a unique name
                    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                    abs_file_path = os.path.join(abs_profile_pics_dir, unique_filename)
                    form.profile_picture.data.save(abs_file_path)
                    
                    # Ensure proper file permissions
                    os.chmod(abs_file_path, 0o666)  # rw-rw-rw- permissions
                    
                    # Update the user's profile picture field
                    current_user.profile_picture = f"uploads/profile_pics/{unique_filename}"
                    flash('Profile picture updated successfully!', 'success')
            except Exception as e:
                import traceback
                print(f"Error saving profile picture: {str(e)}")
                print(traceback.format_exc())
                flash(f'Error uploading profile picture: {str(e)}', 'danger')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.profile'))
    
    return render_template('user/profile.html', form=form)

# Medication tracking responses
@user.route('/medication-response', methods=['POST'])
def medication_response():
    # This would be called by Twilio webhook
    # Process SMS responses (YES/NO) for medication reminders
    pass

@user.route('/test-twilio', methods=['GET', 'POST'])
@login_required
def test_twilio():
    form = TwilioTestForm()
    success_message = None
    error_message = None
    error_details = None
    delivery_warning = None
    
    twilio_config = {
        'account_sid': os.environ.get('TWILIO_ACCOUNT_SID'),
        'auth_token': os.environ.get('TWILIO_AUTH_TOKEN'),
        'phone_number': os.environ.get('TWILIO_PHONE_NUMBER')
    }
    
    if form.validate_on_submit():
        try:
            # Log the request attempt
            TwilioLogger.log_request(form.phone_number.data, form.message.data, twilio_config)
            
            # Check for missing configuration
            if not twilio_config['account_sid']:
                raise ValueError("Twilio Account SID is not configured. Check your .env file.")
            if not twilio_config['auth_token']:
                raise ValueError("Twilio Auth Token is not configured. Check your .env file.")
            if not twilio_config['phone_number']:
                raise ValueError("Twilio Phone Number is not configured. Check your .env file.")
            
            # Check if the phone number is properly formatted
            if not form.phone_number.data.startswith('+'):
                form.phone_number.data = '+' + form.phone_number.data
                delivery_warning = "Phone number didn't start with '+', prepended automatically. Make sure you're using E.164 format."
            
            # Setup Twilio client
            client = Client(twilio_config['account_sid'], twilio_config['auth_token'])
            
            # Send message
            message = client.messages.create(
                body=form.message.data,
                from_=twilio_config['phone_number'],
                to=form.phone_number.data
            )
            
            # Log success
            TwilioLogger.log_success(form.phone_number.data, message.sid, {
                'status': message.status,
                'direction': message.direction,
                'date_created': str(message.date_created)
            })
            
            success_message = f"Message accepted by Twilio! SID: {message.sid}"
            
            # Check account type and provide warnings
            try:
                account = client.api.accounts(twilio_config['account_sid']).fetch()
                if account.type == "Trial":
                    delivery_warning = ("You're using a Twilio trial account. Messages can only be sent to verified phone numbers. "
                                      "Please verify the recipient number in your Twilio console: "
                                      "https://www.twilio.com/console/phone-numbers/verified")
            except Exception as e:
                # Non-fatal error, just log it
                current_app.logger.error(f"Error checking Twilio account type: {str(e)}")
                
        except TwilioRestException as e:
            # Log Twilio-specific error
            error_code = getattr(e, 'code', None)
            TwilioLogger.log_error(form.phone_number.data, str(e), error_code, twilio_config)
            
            # Provide user-friendly error message
            error_message = "Twilio Error: Could not send message."
            error_details = {
                'code': error_code,
                'message': str(e),
                'more_info': getattr(e, 'more_info', None),
                'status': getattr(e, 'status', None)
            }
            
            # Special handling for common Twilio errors
            if error_code == 21608:
                error_message = "Error: This phone number isn't verified with your Twilio trial account."
            elif error_code == 21211:
                error_message = "Error: Invalid 'To' Phone Number format. Use E.164 format (e.g., +1XXXXXXXXXX)."
            elif error_code == 20003:
                error_message = "Error: Authentication failed. Check your Twilio credentials."
                
        except ValueError as e:
            # Configuration error
            TwilioLogger.log_error(form.phone_number.data, str(e), 'CONFIG_ERROR', twilio_config)
            error_message = f"Configuration Error: {str(e)}"
        except Exception as e:
            # Other unexpected errors
            TwilioLogger.log_error(form.phone_number.data, str(e), 'UNEXPECTED_ERROR', twilio_config)
            error_message = f"Unexpected Error: {str(e)}"
    
    # Get recent logs for display
    recent_logs = TwilioLogger.get_recent_logs(limit=10)
    
    # Calculate account type
    account_type = None
    try:
        client = Client(twilio_config['account_sid'], twilio_config['auth_token'])
        account = client.api.accounts(twilio_config['account_sid']).fetch()
        account_type = account.type
    except:
        pass
    
    return render_template('user/twilio_test.html', 
                          form=form, 
                          success_message=success_message, 
                          error_message=error_message,
                          error_details=error_details,
                          delivery_warning=delivery_warning,
                          account_type=account_type,
                          recent_logs=recent_logs,
                          twilio_config={
                              'account_sid': bool(twilio_config['account_sid']),
                              'auth_token': bool(twilio_config['auth_token']),
                              'phone_number': bool(twilio_config['phone_number'])
                          })

@user.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        
        if form.profile_picture.data and hasattr(form.profile_picture.data, 'filename'):
            try:
                # Generate upload paths
                static_dir = os.path.join('app', 'static')
                uploads_dir = os.path.join(static_dir, 'uploads')
                profile_pics_dir = os.path.join(uploads_dir, 'profile_pics')
                
                # Create directories if they don't exist - use absolute paths
                abs_static_dir = os.path.join('/app', static_dir)
                abs_uploads_dir = os.path.join('/app', uploads_dir)
                abs_profile_pics_dir = os.path.join('/app', profile_pics_dir)
                
                # Create each directory in sequence
                if not os.path.exists(abs_static_dir):
                    os.makedirs(abs_static_dir)
                if not os.path.exists(abs_uploads_dir):
                    os.makedirs(abs_uploads_dir)
                if not os.path.exists(abs_profile_pics_dir):
                    os.makedirs(abs_profile_pics_dir)
                
                # Generate a unique filename
                original_filename = secure_filename(form.profile_picture.data.filename)
                file_ext = os.path.splitext(original_filename)[1].lower()
                # Only allow certain extensions
                if file_ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                    flash('Only JPG, JPEG, PNG, and GIF files are allowed!', 'danger')
                else:
                    # Save the file with a unique name
                    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
                    abs_file_path = os.path.join(abs_profile_pics_dir, unique_filename)
                    form.profile_picture.data.save(abs_file_path)
                    
                    # Ensure proper file permissions
                    os.chmod(abs_file_path, 0o666)  # rw-rw-rw- permissions
                    
                    # Update the user's profile picture field
                    current_user.profile_picture = f"uploads/profile_pics/{unique_filename}"
                    flash('Profile picture updated successfully!', 'success')
            except Exception as e:
                import traceback
                print(f"Error saving profile picture: {str(e)}")
                print(traceback.format_exc())
                flash(f'Error uploading profile picture: {str(e)}', 'danger')
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('user.profile'))
    
    return render_template('user/edit_profile.html', form=form)

@user.route('/twilio-logs')
@login_required
def twilio_logs():
    """View all Twilio logs"""
    # All authenticated users can view logs
    # We might filter by user_id in the future, but for now, show all logs
    logs = TwilioLogger.get_recent_logs(limit=100)
    
    return render_template('user/twilio_logs.html', logs=logs)

@user.route('/direct-twilio-test', methods=['GET', 'POST'])
@login_required
def direct_twilio_test():
    """Test Twilio connectivity with direct API calls"""
    form = TwilioTestForm()
    result = None
    curl_command = None
    
    if form.validate_on_submit():
        account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        from_number = os.environ.get('TWILIO_PHONE_NUMBER')
        to_number = form.phone_number.data
        message_body = form.message.data
        
        # Generate curl command for debugging
        curl_command = f"""curl 'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json' \\
-X POST \\
--data-urlencode 'To={to_number}' \\
--data-urlencode 'From={from_number}' \\
--data-urlencode 'Body={message_body}' \\
-u {account_sid}:{auth_token}"""

        # Make a direct HTTP request to Twilio API
        try:
            url = f'https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json'
            auth = (account_sid, auth_token)
            data = {
                'To': to_number,
                'From': from_number,
                'Body': message_body
            }
            
            response = requests.post(url, data=data, auth=auth)
            result = {
                'status_code': response.status_code,
                'response_text': response.text,
                'headers': dict(response.headers)
            }
            
            # Log the direct API test
            TwilioLogger.log_request(to_number, message_body, {
                'account_sid': account_sid,
                'auth_token': auth_token,
                'phone_number': from_number
            })
            
            if response.status_code == 201:
                # Success
                response_json = response.json()
                TwilioLogger.log_success(to_number, response_json.get('sid'), response_json)
                flash('Direct API test successful! Check the response details below.', 'success')
            else:
                # Error
                TwilioLogger.log_error(to_number, response.text, response.status_code)
                flash('Direct API test failed. See details below.', 'danger')
                
        except Exception as e:
            TwilioLogger.log_error(to_number, str(e), 'DIRECT_API_ERROR')
            result = {
                'error': str(e),
                'type': type(e).__name__
            }
            flash(f'Error making direct API request: {str(e)}', 'danger')
    
    return render_template('user/direct_twilio_test.html', 
                          form=form,
                          result=result,
                          curl_command=curl_command)

@user.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # Verify current password
        if current_user.verify_password(form.old_password.data):
            # Set new password
            current_user.password = form.password.data
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('user.profile'))
        else:
            flash('Current password is incorrect', 'danger')
    
    return render_template('user/change_password.html', form=form) 