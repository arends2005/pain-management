from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, g, abort
from flask_login import login_required, current_user
from datetime import datetime, date, timedelta
from app.extensions import db
from app.models.user import User, TextPreference, DiscordPreference, SystemSettings
from app.models.injury import Injury, ProgressLog
from app.models.recovery_plan import RecoveryPlan, Medication, Exercise, MedicationDose, ExerciseSession, Reminder, DiscordInteractionLog
from app.forms.user_forms import (InjuryForm, ProgressLogForm, RecoveryPlanForm, 
                                MedicationForm, ExerciseForm, TextPreferenceForm, ProfileForm, TwilioTestForm,
                                DiscordPreferenceForm)
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
    all_plans = RecoveryPlan.query.filter_by(user_id=current_user.id).all()
    active_plans = [plan for plan in all_plans if plan.is_active]
    past_plans = [plan for plan in all_plans if not plan.is_active]
    return render_template('user/recovery_plans/index.html', 
                          active_plans=active_plans,
                          past_plans=past_plans)

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
    plan = RecoveryPlan.query.get_or_404(id)
    if plan.user_id != current_user.id:
        flash('You do not have permission to view this recovery plan.', 'danger')
        return redirect(url_for('user.recovery_plans'))
    
    medications = Medication.query.filter_by(recovery_plan_id=plan.id).all()
    exercises = Exercise.query.filter_by(recovery_plan_id=plan.id).all()
    
    return render_template('user/recovery_plans/show.html', plan=plan, 
                           medications=medications, exercises=exercises,
                           timedelta=timedelta, user=current_user)

@user.route('/recovery-plans/<int:plan_id>/medications/new', methods=['GET', 'POST'])
@login_required
def new_medication(plan_id):
    plan = RecoveryPlan.query.get_or_404(plan_id)
    
    # Ensure the user owns this recovery plan
    if plan.user_id != current_user.id:
        flash('You do not have permission to add medications to this plan.', 'danger')
        return redirect(url_for('user.recovery_plans'))
    
    form = MedicationForm()
    
    if form.validate_on_submit():
        medication = Medication(
            recovery_plan_id=plan.id,
            name=form.name.data,
            dosage=form.dosage.data,
            frequency=form.frequency.data,
            instructions=form.instructions.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data,
            discord_notifications=form.discord_notifications.data
        )
        db.session.add(medication)
        db.session.commit()
        flash('Medication added successfully!', 'success')
        return redirect(url_for('user.show_recovery_plan', id=plan.id))
    
    return render_template('user/medications/new.html', form=form, plan=plan)

@user.route('/recovery-plans/<int:plan_id>/exercises/new', methods=['GET', 'POST'])
@login_required
def new_exercise(plan_id):
    plan = RecoveryPlan.query.get_or_404(plan_id)
    
    # Ensure the user owns this recovery plan
    if plan.user_id != current_user.id:
        flash('You do not have permission to add exercises to this plan.', 'danger')
        return redirect(url_for('user.recovery_plans'))
    
    form = ExerciseForm()
    
    if form.validate_on_submit():
        exercise = Exercise(
            recovery_plan_id=plan.id,
            name=form.name.data,
            description=form.description.data,
            frequency=form.frequency.data,
            duration=form.duration.data,
            repetitions=form.repetitions.data,
            instructions=form.instructions.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data,
            discord_notifications=form.discord_notifications.data
        )
        db.session.add(exercise)
        db.session.commit()
        flash('Exercise added successfully!', 'success')
        return redirect(url_for('user.show_recovery_plan', id=plan.id))
    
    return render_template('user/exercises/new.html', form=form, plan=plan)

@user.route('/medications/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_medication(id):
    medication = Medication.query.get_or_404(id)
    plan = RecoveryPlan.query.get_or_404(medication.recovery_plan_id)
    
    # Ensure the user owns this medication
    if plan.user_id != current_user.id:
        flash('You do not have permission to edit this medication.', 'danger')
        return redirect(url_for('user.recovery_plans'))
    
    form = MedicationForm(obj=medication)
    
    if form.validate_on_submit():
        form.populate_obj(medication)
        db.session.commit()
        flash('Medication updated successfully!', 'success')
        return redirect(url_for('user.show_recovery_plan', id=plan.id))
    
    return render_template('user/medications/edit.html', form=form, medication=medication, plan=plan)

@user.route('/exercises/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_exercise(id):
    exercise = Exercise.query.get_or_404(id)
    plan = RecoveryPlan.query.get_or_404(exercise.recovery_plan_id)
    
    # Ensure the user owns this exercise
    if plan.user_id != current_user.id:
        flash('You do not have permission to edit this exercise.', 'danger')
        return redirect(url_for('user.recovery_plans'))
    
    form = ExerciseForm(obj=exercise)
    
    if form.validate_on_submit():
        form.populate_obj(exercise)
        db.session.commit()
        flash('Exercise updated successfully!', 'success')
        return redirect(url_for('user.show_recovery_plan', id=plan.id))
    
    return render_template('user/exercises/edit.html', form=form, exercise=exercise, plan=plan)

@user.route('/medications/<int:id>/test-notification', methods=['POST'])
@login_required
def test_medication_notification(id):
    """Test sending a Discord notification for a medication"""
    medication = Medication.query.get_or_404(id)
    plan = RecoveryPlan.query.get_or_404(medication.recovery_plan_id)
    
    # Ensure the user owns this medication
    if plan.user_id != current_user.id:
        flash('You do not have permission to test this medication.', 'danger')
        return redirect(url_for('user.recovery_plans'))
    
    # Check if the user has Discord preferences set up
    discord_pref = current_user.discord_preferences
    
    if not discord_pref or not discord_pref.discord_channel_id:
        flash('You must set up your Discord preferences with a valid Channel ID first.', 'warning')
        return redirect(url_for('user.discord_preferences'))
    
    # Create a medication-specific test message with plan name
    message = f"**Medication Reminder TEST**\n\n📋 Plan: {plan.name}\n📋 {medication.name}\n💊 Dosage: {medication.dosage}\n⏰ Every {medication.frequency} hours\n\n{medication.instructions if medication.instructions else ''}\n\nThis is a TEST message. No response is required."
    
    # Create a log entry for the test message
    log = DiscordInteractionLog(
        user_id=current_user.id,
        discord_channel_id=discord_pref.discord_channel_id,
        message_type='test',
        medication_id=medication.id,
        sent_message=message,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Test medication notification has been queued. It will be sent to the Discord channel within the next minute.', 'success')
    return redirect(url_for('user.edit_medication', id=medication.id))

@user.route('/exercises/<int:id>/test-notification', methods=['POST'])
@login_required
def test_exercise_notification(id):
    """Test sending a Discord notification for an exercise"""
    exercise = Exercise.query.get_or_404(id)
    plan = RecoveryPlan.query.get_or_404(exercise.recovery_plan_id)
    
    # Ensure the user owns this exercise
    if plan.user_id != current_user.id:
        flash('You do not have permission to test this exercise.', 'danger')
        return redirect(url_for('user.recovery_plans'))
    
    # Check if the user has Discord preferences set up
    discord_pref = current_user.discord_preferences
    
    if not discord_pref or not discord_pref.discord_channel_id:
        flash('You must set up your Discord preferences with a valid Channel ID first.', 'warning')
        return redirect(url_for('user.discord_preferences'))
    
    # Create an exercise-specific test message with plan name
    message = f"**Exercise Reminder TEST**\n\n📋 Plan: {plan.name}\n🏋️ {exercise.name}\n⏱️ Duration: {exercise.duration if exercise.duration else 'N/A'}\n🔄 Repetitions: {exercise.repetitions if exercise.repetitions else 'N/A'}\n⏰ Every {exercise.frequency} hours\n\n{exercise.instructions if exercise.instructions else ''}\n\nThis is a TEST message. No response is required."
    
    # Create a log entry for the test message
    log = DiscordInteractionLog(
        user_id=current_user.id,
        discord_channel_id=discord_pref.discord_channel_id,
        message_type='test',
        exercise_id=exercise.id,
        sent_message=message,
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
    
    flash('Test exercise notification has been queued. It will be sent to the Discord channel within the next minute.', 'success')
    return redirect(url_for('user.edit_exercise', id=exercise.id))

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

@user.route('/discord-preferences', methods=['GET', 'POST'])
@login_required
def discord_preferences():
    discord_pref = DiscordPreference.query.filter_by(user_id=current_user.id).first()
    if not discord_pref:
        discord_pref = DiscordPreference(
            user_id=current_user.id, 
            enabled=True
        )
        db.session.add(discord_pref)
        db.session.commit()
    
    form = DiscordPreferenceForm(obj=discord_pref)
    
    if form.validate_on_submit():
        form.populate_obj(discord_pref)
        db.session.commit()
        flash('Discord preferences updated successfully!', 'success')
        return redirect(url_for('user.profile'))
    
    # Get the Discord invite URL from system settings
    discord_invite_url = SystemSettings.get_setting('DISCORD_INVITE_URL', 
                                                  current_app.config.get('DISCORD_INVITE_URL', ''))
    
    return render_template('user/discord_preferences.html', form=form, discord_invite_url=discord_invite_url)

@user.route('/test-discord-connection', methods=['POST'])
@login_required
def test_discord_connection():
    """Test Discord connection for the current user"""
    # Check if they have Discord settings
    discord_pref = current_user.discord_preferences
    
    if not discord_pref or not discord_pref.discord_channel_id:
        flash('You must set up your Discord preferences with a valid Channel ID first.', 'warning')
        return redirect(url_for('user.discord_preferences'))

    # Create a log entry for the test message
    log = DiscordInteractionLog(
        user_id=current_user.id,
        discord_channel_id=discord_pref.discord_channel_id,
        message_type='test',
        sent_message='This is a test of the bot connection',
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
    
    success_message = 'Test message queued! Please check your Discord server channel in the next minute.'
    
    if request.is_json:
        return jsonify({'success': True, 'message': success_message})
    
    flash(success_message, 'success')
    return redirect(url_for('user.discord_preferences'))

@user.route('/medications/<int:id>/delete', methods=['POST'])
@login_required
def delete_medication(id):
    medication = Medication.query.get_or_404(id)
    plan = RecoveryPlan.query.get_or_404(medication.recovery_plan_id)
    
    # Ensure the user owns this medication
    if plan.user_id != current_user.id:
        flash('You do not have permission to delete this medication.', 'danger')
        return redirect(url_for('user.recovery_plans'))
    
    db.session.delete(medication)
    db.session.commit()
    flash('Medication deleted successfully!', 'success')
    return redirect(url_for('user.show_recovery_plan', id=plan.id))

@user.route('/exercises/<int:id>/delete', methods=['POST'])
@login_required
def delete_exercise(id):
    exercise = Exercise.query.get_or_404(id)
    plan = RecoveryPlan.query.get_or_404(exercise.recovery_plan_id)
    
    # Ensure the user owns this exercise
    if plan.user_id != current_user.id:
        flash('You do not have permission to delete this exercise.', 'danger')
        return redirect(url_for('user.recovery_plans'))
    
    db.session.delete(exercise)
    db.session.commit()
    flash('Exercise deleted successfully!', 'success')
    return redirect(url_for('user.show_recovery_plan', id=plan.id))

@user.route('/recovery-plans/<int:id>/chart-data')
@login_required
def recovery_plan_chart_data(id):
    plan = RecoveryPlan.query.get_or_404(id)
    if plan.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get data for the last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Get all medications and exercises
    medications = Medication.query.filter_by(recovery_plan_id=plan.id, is_active=True).all()
    exercises = Exercise.query.filter_by(recovery_plan_id=plan.id, is_active=True).all()
    
    # Prepare data points for each day
    data = []
    current_date = start_date
    
    # Check if we have any data
    has_data = False
    if medications or exercises:
        has_data = True
    
    while current_date <= end_date:
        day_start = datetime(current_date.year, current_date.month, current_date.day, 0, 0, 0)
        day_end = datetime(current_date.year, current_date.month, current_date.day, 23, 59, 59)
        
        if has_data:
            # Count medication doses that were scheduled for this day
            med_total = 0
            med_taken = 0
            
            # Get all interaction logs for medications on this day
            med_logs = DiscordInteractionLog.query.filter(
                DiscordInteractionLog.user_id == current_user.id,
                DiscordInteractionLog.message_type == 'medication',
                DiscordInteractionLog.timestamp >= day_start,
                DiscordInteractionLog.timestamp <= day_end
            ).all()
            
            # Count all medications that were asked about
            med_total = len(med_logs)
            
            # Count those that were completed
            med_taken = sum(1 for log in med_logs if log.completed)
            
            # If there are no medication logs but we have medications configured,
            # check if there are any recorded doses for the day
            if med_total == 0 and medications:
                for med in medications:
                    # Estimate doses that should have been taken
                    daily_doses = 24 // med.frequency if med.frequency > 0 else 0
                    med_total += daily_doses
                    
                    # Count actual doses taken
                    doses_taken = MedicationDose.query.filter(
                        MedicationDose.medication_id == med.id,
                        MedicationDose.timestamp >= day_start,
                        MedicationDose.timestamp <= day_end,
                        MedicationDose.taken == True
                    ).count()
                    med_taken += doses_taken
            
            # Count exercise sessions that were scheduled for this day
            ex_total = 0
            ex_completed = 0
            
            # Get all interaction logs for exercises on this day
            ex_logs = DiscordInteractionLog.query.filter(
                DiscordInteractionLog.user_id == current_user.id,
                DiscordInteractionLog.message_type == 'exercise',
                DiscordInteractionLog.timestamp >= day_start,
                DiscordInteractionLog.timestamp <= day_end
            ).all()
            
            # Count all exercises that were asked about
            ex_total = len(ex_logs)
            
            # Count those that were completed
            ex_completed = sum(1 for log in ex_logs if log.completed)
            
            # If there are no exercise logs but we have exercises configured,
            # check if there are any recorded sessions for the day
            if ex_total == 0 and exercises:
                for ex in exercises:
                    # Estimate sessions that should have been done
                    daily_sessions = 24 // ex.frequency if ex.frequency > 0 else 0
                    ex_total += daily_sessions
                    
                    # Count actual sessions completed
                    sessions_completed = ExerciseSession.query.filter(
                        ExerciseSession.exercise_id == ex.id,
                        ExerciseSession.timestamp >= day_start,
                        ExerciseSession.timestamp <= day_end,
                        ExerciseSession.completed == True
                    ).count()
                    ex_completed += sessions_completed
            
            # Calculate adherence percentages - handle the case where nothing was asked or recorded
            if med_total == 0:
                med_adherence = 100 if current_date.date() < datetime.now().date() else 0
            else:
                med_adherence = round((med_taken / med_total) * 100)
                
            if ex_total == 0:
                ex_adherence = 100 if current_date.date() < datetime.now().date() else 0
            else:
                ex_adherence = round((ex_completed / ex_total) * 100)
                
            if med_total + ex_total == 0:
                total_adherence = 100 if current_date.date() < datetime.now().date() else 0
            else:
                total_adherence = round(((med_taken + ex_completed) / (med_total + ex_total)) * 100)
        else:
            # Generate sample data if no real data exists
            # This ensures the chart still displays something
            day_num = (current_date - start_date).days
            
            # Create a pattern that shows improvement over time
            med_total = 4
            ex_total = 2
            
            # Start with lower values and gradually improve
            base_med_taken = min(med_total, 1 + day_num // 2)
            base_ex_completed = min(ex_total, 1 + day_num // 3)
            
            # Add some randomness
            import random
            med_taken = min(med_total, max(0, base_med_taken + random.randint(-1, 1)))
            ex_completed = min(ex_total, max(0, base_ex_completed + random.randint(-1, 1)))
            
            # Calculate adherence percentages
            med_adherence = round((med_taken / max(1, med_total)) * 100)
            ex_adherence = round((ex_completed / max(1, ex_total)) * 100)
            total_adherence = round(((med_taken + ex_completed) / max(1, med_total + ex_total)) * 100)
        
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'medication_adherence': med_adherence,
            'exercise_adherence': ex_adherence,
            'total_adherence': total_adherence,
            'medication_total': med_total,
            'medication_taken': med_taken,
            'exercise_total': ex_total,
            'exercise_completed': ex_completed
        })
        
        current_date += timedelta(days=1)
    
    return jsonify({
        'plan_name': plan.name,
        'data': data
    })

@user.route('/recovery-plans/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_recovery_plan(id):
    plan = RecoveryPlan.query.get_or_404(id)
    
    # Ensure the user owns this recovery plan
    if plan.user_id != current_user.id:
        flash('You do not have permission to edit this recovery plan.', 'danger')
        return redirect(url_for('user.recovery_plans'))
    
    form = RecoveryPlanForm(obj=plan)
    form.injury_id.choices = [(i.id, i.name) for i in Injury.query.filter_by(user_id=current_user.id).all()]
    
    if form.validate_on_submit():
        form.populate_obj(plan)
        db.session.commit()
        flash('Recovery plan updated successfully!', 'success')
        return redirect(url_for('user.show_recovery_plan', id=plan.id))
    
    return render_template('user/recovery_plans/edit.html', form=form, plan=plan)

@user.route('/recovery-plans/<int:id>/history', methods=['GET'])
@login_required
def recovery_plan_history(id):
    plan = RecoveryPlan.query.get_or_404(id)
    
    # Ensure the user owns this recovery plan
    if plan.user_id != current_user.id:
        flash('You do not have permission to view this recovery plan history.', 'danger')
        return redirect(url_for('user.recovery_plans'))
    
    # Default to showing the last 7 days, but allow adjusting via query params
    days = request.args.get('days', 7, type=int)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Get all medications and exercises for this plan
    medications = Medication.query.filter_by(recovery_plan_id=plan.id).all()
    exercises = Exercise.query.filter_by(recovery_plan_id=plan.id).all()
    
    # Prepare data for all days in the range
    history_data = []
    
    current_date = start_date
    while current_date <= end_date:
        day_start = datetime(current_date.year, current_date.month, current_date.day, 0, 0, 0)
        day_end = datetime(current_date.year, current_date.month, current_date.day, 23, 59, 59)
        
        # Collect medication data
        med_entries = []
        for med in medications:
            # Check if the medication was active on this date
            if (med.start_date <= current_date.date() and 
                (med.end_date is None or med.end_date >= current_date.date()) and
                med.is_active):
                
                # Calculate expected doses for this day based on frequency
                expected_doses = 24 // med.frequency if med.frequency > 0 else 0
                
                # Get actual recorded doses
                doses = MedicationDose.query.filter(
                    MedicationDose.medication_id == med.id,
                    MedicationDose.timestamp >= day_start,
                    MedicationDose.timestamp <= day_end
                ).all()
                
                # Get Discord logs for this medication
                discord_logs = DiscordInteractionLog.query.filter(
                    DiscordInteractionLog.medication_id == med.id,
                    DiscordInteractionLog.timestamp >= day_start,
                    DiscordInteractionLog.timestamp <= day_end
                ).all()
                
                # For each expected dose, create an entry
                for i in range(expected_doses):
                    # Calculate expected time (roughly)
                    expected_hour = (i * med.frequency) % 24
                    expected_time = day_start + timedelta(hours=expected_hour)
                    
                    # Check if we have a matching dose record
                    matching_dose = next((d for d in doses if 
                                         abs((d.timestamp - expected_time).total_seconds()) < med.frequency * 3600/2), 
                                        None)
                    
                    # Check for a matching Discord log
                    matching_log = next((l for l in discord_logs if 
                                        abs((l.timestamp - expected_time).total_seconds()) < med.frequency * 3600/2),
                                       None)
                    
                    entry = {
                        'type': 'medication',
                        'id': med.id,
                        'name': med.name,
                        'expected_time': expected_time,
                        'dose_id': matching_dose.id if matching_dose else None,
                        'log_id': matching_log.id if matching_log else None,
                        'taken': matching_dose.taken if matching_dose else (matching_log.completed if matching_log else False),
                        'actual_time': matching_dose.timestamp if matching_dose else (matching_log.timestamp if matching_log else None),
                        'notes': matching_dose.notes if matching_dose else None,
                        'tracking_method': 'app' if matching_dose else ('discord' if matching_log else None)
                    }
                    med_entries.append(entry)
        
        # Collect exercise data
        ex_entries = []
        for ex in exercises:
            # Check if the exercise was active on this date
            if (ex.start_date <= current_date.date() and 
                (ex.end_date is None or ex.end_date >= current_date.date()) and
                ex.is_active):
                
                # Calculate expected sessions for this day based on frequency
                expected_sessions = 24 // ex.frequency if ex.frequency > 0 else 0
                
                # Get actual recorded sessions
                sessions = ExerciseSession.query.filter(
                    ExerciseSession.exercise_id == ex.id,
                    ExerciseSession.timestamp >= day_start,
                    ExerciseSession.timestamp <= day_end
                ).all()
                
                # Get Discord logs for this exercise
                discord_logs = DiscordInteractionLog.query.filter(
                    DiscordInteractionLog.exercise_id == ex.id,
                    DiscordInteractionLog.timestamp >= day_start,
                    DiscordInteractionLog.timestamp <= day_end
                ).all()
                
                # For each expected session, create an entry
                for i in range(expected_sessions):
                    # Calculate expected time (roughly)
                    expected_hour = (i * ex.frequency) % 24
                    expected_time = day_start + timedelta(hours=expected_hour)
                    
                    # Check if we have a matching session record
                    matching_session = next((s for s in sessions if 
                                            abs((s.timestamp - expected_time).total_seconds()) < ex.frequency * 3600/2), 
                                           None)
                    
                    # Check for a matching Discord log
                    matching_log = next((l for l in discord_logs if 
                                        abs((l.timestamp - expected_time).total_seconds()) < ex.frequency * 3600/2),
                                       None)
                    
                    entry = {
                        'type': 'exercise',
                        'id': ex.id,
                        'name': ex.name,
                        'expected_time': expected_time,
                        'session_id': matching_session.id if matching_session else None,
                        'log_id': matching_log.id if matching_log else None,
                        'completed': matching_session.completed if matching_session else (matching_log.completed if matching_log else False),
                        'actual_time': matching_session.timestamp if matching_session else (matching_log.timestamp if matching_log else None),
                        'notes': matching_session.notes if matching_session else None,
                        'difficulty': matching_session.difficulty if matching_session else None,
                        'tracking_method': 'app' if matching_session else ('discord' if matching_log else None)
                    }
                    ex_entries.append(entry)
        
        # Calculate day's adherence
        med_total = len(med_entries)
        med_taken = sum(1 for e in med_entries if e['taken'])
        ex_total = len(ex_entries)
        ex_completed = sum(1 for e in ex_entries if e['completed'])
        
        med_adherence = round((med_taken / max(1, med_total)) * 100)
        ex_adherence = round((ex_completed / max(1, ex_total)) * 100)
        overall_adherence = round(((med_taken + ex_completed) / max(1, med_total + ex_total)) * 100)
        
        # Add day data to history
        history_data.append({
            'date': current_date.date(),
            'medication_entries': med_entries,
            'exercise_entries': ex_entries,
            'medication_adherence': med_adherence,
            'exercise_adherence': ex_adherence,
            'overall_adherence': overall_adherence
        })
        
        current_date += timedelta(days=1)
    
    return render_template('user/recovery_plans/history.html', 
                          plan=plan, 
                          history_data=history_data,
                          days=days)

@user.route('/recovery-plans/update-activity', methods=['POST'])
@login_required
def update_activity():
    data = request.get_json()
    activity_type = data.get('type')
    activity_id = data.get('id')
    new_status = data.get('status')
    notes = data.get('notes', '')
    
    if activity_type == 'medication':
        dose = MedicationDose.query.get_or_404(activity_id)
        medication = Medication.query.get_or_404(dose.medication_id)
        plan = RecoveryPlan.query.get_or_404(medication.recovery_plan_id)
        
        # Check if user owns this plan
        if plan.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        dose.taken = new_status
        dose.notes = notes
        dose.response_time = datetime.now()
    
    elif activity_type == 'exercise':
        session = ExerciseSession.query.get_or_404(activity_id)
        exercise = Exercise.query.get_or_404(session.exercise_id)
        plan = RecoveryPlan.query.get_or_404(exercise.recovery_plan_id)
        
        # Check if user owns this plan
        if plan.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        session.completed = new_status
        session.notes = notes
        session.response_time = datetime.now()
        session.difficulty = data.get('difficulty')
    
    elif activity_type == 'new_medication':
        medication_id = data.get('medication_id')
        medication = Medication.query.get_or_404(medication_id)
        plan = RecoveryPlan.query.get_or_404(medication.recovery_plan_id)
        
        # Check if user owns this plan
        if plan.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Create a new dose
        new_dose = MedicationDose(
            medication_id=medication_id,
            timestamp=datetime.fromisoformat(data.get('timestamp')),
            taken=new_status,
            notes=notes,
            response_time=datetime.now()
        )
        db.session.add(new_dose)
        activity_id = new_dose.id  # This will be None until after commit
    
    elif activity_type == 'new_exercise':
        exercise_id = data.get('exercise_id')
        exercise = Exercise.query.get_or_404(exercise_id)
        plan = RecoveryPlan.query.get_or_404(exercise.recovery_plan_id)
        
        # Check if user owns this plan
        if plan.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        # Create a new session
        new_session = ExerciseSession(
            exercise_id=exercise_id,
            timestamp=datetime.fromisoformat(data.get('timestamp')),
            completed=new_status,
            notes=notes,
            difficulty=data.get('difficulty'),
            response_time=datetime.now()
        )
        db.session.add(new_session)
        activity_id = new_session.id  # This will be None until after commit
    
    else:
        return jsonify({'success': False, 'message': 'Invalid activity type'}), 400
    
    db.session.commit()
    
    # After commit, get the ID for newly created records
    if activity_type in ('new_medication', 'new_exercise'):
        activity_id = new_dose.id if activity_type == 'new_medication' else new_session.id
    
    return jsonify({
        'success': True, 
        'message': 'Activity updated successfully',
        'activity_id': activity_id
    }) 