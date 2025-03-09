from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from app.extensions import db
from app.models.user import User, TextPreference
from app.models.injury import Injury, ProgressLog
from app.models.recovery_plan import RecoveryPlan, Medication, Exercise
from app.forms.user_forms import (InjuryForm, ProgressLogForm, RecoveryPlanForm, 
                                MedicationForm, ExerciseForm, TextPreferenceForm, ProfileForm)
from app.forms.admin_forms import UserForm, CreateUserForm
import logging

# Configure logger
logger = logging.getLogger(__name__)

admin = Blueprint('admin', __name__)

# Admin access decorator
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@admin.route('/dashboard')
@admin_required
def dashboard():
    users_count = User.query.filter_by(is_admin=False).count()
    injuries_count = Injury.query.count()
    recovery_plans_count = RecoveryPlan.query.count()
    active_plans_count = RecoveryPlan.query.filter_by(is_active=True).count()
    
    # Recent users
    recent_users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                          users_count=users_count,
                          injuries_count=injuries_count,
                          recovery_plans_count=recovery_plans_count,
                          active_plans_count=active_plans_count,
                          recent_users=recent_users)

# User Management
@admin.route('/users')
@admin_required
def users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users/index.html', users=users)

@admin.route('/users/<int:id>')
@admin_required
def show_user(id):
    user = User.query.get_or_404(id)
    injuries = Injury.query.filter_by(user_id=user.id).all()
    recovery_plans = RecoveryPlan.query.filter_by(user_id=user.id).all()
    return render_template('admin/users/show.html', 
                          user=user, 
                          injuries=injuries, 
                          recovery_plans=recovery_plans)

@admin.route('/users/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.phone_number = form.phone_number.data
        
        if form.password.data:
            user.password = form.password.data
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.show_user', id=user.id))
    
    return render_template('admin/users/edit.html', form=form, user=user)

# Injury Management
@admin.route('/users/<int:user_id>/injuries')
@admin_required
def user_injuries(user_id):
    user = User.query.get_or_404(user_id)
    injuries = Injury.query.filter_by(user_id=user.id).all()
    return render_template('admin/injuries/index.html', user=user, injuries=injuries)

@admin.route('/users/<int:user_id>/injuries/new', methods=['GET', 'POST'])
@admin_required
def new_user_injury(user_id):
    user = User.query.get_or_404(user_id)
    form = InjuryForm()
    
    if request.method == 'POST':
        logger.info(f"Form data received: {request.form}")
        
    if form.validate_on_submit():
        logger.info("Form validated successfully")
        injury = Injury(
            user_id=user.id,
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
        return redirect(url_for('admin.user_injuries', user_id=user.id))
    elif request.method == 'POST':
        logger.error(f"Form validation failed. Errors: {form.errors}")
    
    return render_template('admin/injuries/new.html', form=form, user=user)

@admin.route('/injuries/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_injury(id):
    injury = Injury.query.get_or_404(id)
    user = User.query.get_or_404(injury.user_id)
    form = InjuryForm(obj=injury)
    
    if form.validate_on_submit():
        form.populate_obj(injury)
        db.session.commit()
        flash('Injury updated successfully!', 'success')
        return redirect(url_for('admin.user_injuries', user_id=user.id))
    
    return render_template('admin/injuries/edit.html', form=form, injury=injury, user=user)

# Recovery Plan Management
@admin.route('/users/<int:user_id>/recovery-plans')
@admin_required
def user_recovery_plans(user_id):
    user = User.query.get_or_404(user_id)
    active_plans = RecoveryPlan.query.filter_by(user_id=user.id, is_active=True).all()
    inactive_plans = RecoveryPlan.query.filter_by(user_id=user.id, is_active=False).all()
    
    return render_template('admin/recovery_plans/index.html', 
                          user=user, 
                          active_plans=active_plans,
                          inactive_plans=inactive_plans)

@admin.route('/users/<int:user_id>/recovery-plans/new', methods=['GET', 'POST'])
@admin_required
def new_user_recovery_plan(user_id):
    user = User.query.get_or_404(user_id)
    form = RecoveryPlanForm()
    form.injury_id.choices = [(i.id, i.name) for i in Injury.query.filter_by(user_id=user.id).all()]
    
    if request.method == 'POST':
        logger.info(f"Recovery plan form data received: {request.form}")
        
    if form.validate_on_submit():
        logger.info("Recovery plan form validated successfully")
        plan = RecoveryPlan(
            user_id=user.id,
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
        return redirect(url_for('admin.show_recovery_plan', id=plan.id))
    elif request.method == 'POST':
        logger.error(f"Recovery plan form validation failed. Errors: {form.errors}")
    
    form.start_date.data = date.today()
    return render_template('admin/recovery_plans/new.html', form=form, user=user)

@admin.route('/recovery-plans/<int:id>')
@admin_required
def show_recovery_plan(id):
    plan = RecoveryPlan.query.get_or_404(id)
    user = User.query.get_or_404(plan.user_id)
    medications = Medication.query.filter_by(recovery_plan_id=plan.id).all()
    exercises = Exercise.query.filter_by(recovery_plan_id=plan.id).all()
    
    return render_template('admin/recovery_plans/show.html', 
                          plan=plan,
                          user=user,
                          medications=medications,
                          exercises=exercises)

@admin.route('/recovery-plans/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_recovery_plan(id):
    plan = RecoveryPlan.query.get_or_404(id)
    user = User.query.get_or_404(plan.user_id)
    form = RecoveryPlanForm(obj=plan)
    form.injury_id.choices = [(i.id, i.name) for i in Injury.query.filter_by(user_id=user.id).all()]
    
    if form.validate_on_submit():
        form.populate_obj(plan)
        db.session.commit()
        flash('Recovery plan updated successfully!', 'success')
        return redirect(url_for('admin.show_recovery_plan', id=plan.id))
    
    return render_template('admin/recovery_plans/edit.html', form=form, plan=plan, user=user)

@admin.route('/recovery-plans/<int:id>/show.html')
@admin_required
def show_recovery_plan_html(id):
    # Duplicate of show_recovery_plan for handling "show.html" extension URL
    return redirect(url_for('admin.show_recovery_plan', id=id))

# Text Preferences
@admin.route('/users/<int:user_id>/text-preferences', methods=['GET', 'POST'])
@admin_required
def user_text_preferences(user_id):
    user = User.query.get_or_404(user_id)
    text_pref = TextPreference.query.filter_by(user_id=user.id).first()
    
    if not text_pref:
        text_pref = TextPreference(user_id=user.id, enabled=True)
        db.session.add(text_pref)
        db.session.commit()
    
    form = TextPreferenceForm(obj=text_pref)
    
    if form.validate_on_submit():
        form.populate_obj(text_pref)
        db.session.commit()
        flash('Text preferences updated successfully!', 'success')
        return redirect(url_for('admin.show_user', id=user.id))
    
    return render_template('admin/text_preferences.html', form=form, user=user)

# Admin Profile Management
@admin.route('/profile')
@admin_required
def profile():
    """Display admin's own profile"""
    injuries = Injury.query.filter_by(user_id=current_user.id).all()
    recovery_plans = RecoveryPlan.query.filter_by(user_id=current_user.id).all()
    
    return render_template('admin/profile/show.html', 
                          user=current_user, 
                          injuries=injuries, 
                          recovery_plans=recovery_plans)

@admin.route('/profile/edit', methods=['GET', 'POST'])
@admin_required
def edit_profile():
    """Edit admin's own profile"""
    form = ProfileForm(obj=current_user)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.email = form.email.data
        current_user.phone_number = form.phone_number.data
        
        if form.profile_picture.data and hasattr(form.profile_picture.data, 'filename'):
            try:
                # Import necessary modules
                import os
                from werkzeug.utils import secure_filename
                import uuid
                
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
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('admin.profile'))
    
    return render_template('admin/profile/edit.html', form=form)

@admin.route('/profile/change-password', methods=['GET', 'POST'])
@admin_required
def change_password():
    """Change admin's password"""
    from app.forms.auth_forms import ChangePasswordForm
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        if current_user.check_password(form.old_password.data):
            current_user.password = form.password.data
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('admin.profile'))
        else:
            flash('Current password is incorrect.', 'danger')
            
    return render_template('admin/profile/change_password.html', form=form)

# Medication Management
@admin.route('/recovery-plans/<int:plan_id>/medications/new', methods=['GET', 'POST'])
@admin_required
def new_medication(plan_id):
    plan = RecoveryPlan.query.get_or_404(plan_id)
    user = User.query.get_or_404(plan.user_id)
    form = MedicationForm()
    
    if request.method == 'POST':
        logger.info(f"Medication form data received: {request.form}")
        
    if form.validate_on_submit():
        logger.info("Medication form validated successfully")
        medication = Medication(
            recovery_plan_id=plan.id,
            name=form.name.data,
            dosage=form.dosage.data,
            frequency=form.frequency.data,
            instructions=form.instructions.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data
        )
        db.session.add(medication)
        db.session.commit()
        flash('Medication added successfully!', 'success')
        return redirect(url_for('admin.show_recovery_plan', id=plan.id))
    elif request.method == 'POST':
        logger.error(f"Medication form validation failed. Errors: {form.errors}")
    
    form.start_date.data = date.today()
    return render_template('admin/medications/new.html', form=form, plan=plan, user=user)

@admin.route('/medications/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_medication(id):
    medication = Medication.query.get_or_404(id)
    plan = RecoveryPlan.query.get_or_404(medication.recovery_plan_id)
    user = User.query.get_or_404(plan.user_id)
    form = MedicationForm(obj=medication)
    
    if form.validate_on_submit():
        form.populate_obj(medication)
        db.session.commit()
        flash('Medication updated successfully!', 'success')
        return redirect(url_for('admin.show_recovery_plan', id=plan.id))
    
    return render_template('admin/medications/edit.html', form=form, medication=medication, plan=plan, user=user)

# Exercise Management
@admin.route('/recovery-plans/<int:plan_id>/exercises/new', methods=['GET', 'POST'])
@admin_required
def new_exercise(plan_id):
    plan = RecoveryPlan.query.get_or_404(plan_id)
    user = User.query.get_or_404(plan.user_id)
    form = ExerciseForm()
    
    if request.method == 'POST':
        logger.info(f"Exercise form data received: {request.form}")
        
    if form.validate_on_submit():
        logger.info("Exercise form validated successfully")
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
            is_active=form.is_active.data
        )
        db.session.add(exercise)
        db.session.commit()
        flash('Exercise added successfully!', 'success')
        return redirect(url_for('admin.show_recovery_plan', id=plan.id))
    elif request.method == 'POST':
        logger.error(f"Exercise form validation failed. Errors: {form.errors}")
    
    form.start_date.data = date.today()
    return render_template('admin/exercises/new.html', form=form, plan=plan, user=user)

@admin.route('/exercises/<int:id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_exercise(id):
    exercise = Exercise.query.get_or_404(id)
    plan = RecoveryPlan.query.get_or_404(exercise.recovery_plan_id)
    user = User.query.get_or_404(plan.user_id)
    form = ExerciseForm(obj=exercise)
    
    if form.validate_on_submit():
        form.populate_obj(exercise)
        db.session.commit()
        flash('Exercise updated successfully!', 'success')
        return redirect(url_for('admin.show_recovery_plan', id=plan.id))
    
    return render_template('admin/exercises/edit.html', form=form, exercise=exercise, plan=plan, user=user)

# Delete Routes
@admin.route('/recovery-plans/<int:id>/delete', methods=['POST'])
@admin_required
def delete_recovery_plan(id):
    plan = RecoveryPlan.query.get_or_404(id)
    user_id = plan.user_id
    
    try:
        db.session.delete(plan)
        db.session.commit()
        flash('Recovery plan deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting recovery plan: {str(e)}")
        flash('An error occurred while deleting the recovery plan.', 'danger')
    
    return redirect(url_for('admin.user_recovery_plans', user_id=user_id))

@admin.route('/medications/<int:id>/delete', methods=['POST'])
@admin_required
def delete_medication(id):
    medication = Medication.query.get_or_404(id)
    plan_id = medication.recovery_plan_id
    
    try:
        db.session.delete(medication)
        db.session.commit()
        flash('Medication deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting medication: {str(e)}")
        flash('An error occurred while deleting the medication.', 'danger')
    
    return redirect(url_for('admin.show_recovery_plan', id=plan_id))

@admin.route('/exercises/<int:id>/delete', methods=['POST'])
@admin_required
def delete_exercise(id):
    exercise = Exercise.query.get_or_404(id)
    plan_id = exercise.recovery_plan_id
    
    try:
        db.session.delete(exercise)
        db.session.commit()
        flash('Exercise deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting exercise: {str(e)}")
        flash('An error occurred while deleting the exercise.', 'danger')
    
    return redirect(url_for('admin.show_recovery_plan', id=plan_id))

@admin.route('/injuries/<int:id>/delete', methods=['POST'])
@admin_required
def delete_injury(id):
    injury = Injury.query.get_or_404(id)
    user_id = injury.user_id
    
    # Check if there are any recovery plans associated with this injury
    recovery_plans = RecoveryPlan.query.filter_by(injury_id=injury.id).all()
    
    # Check if cascade_delete is requested
    cascade_delete = request.form.get('cascade_delete') == 'true'
    
    if recovery_plans and not cascade_delete:
        flash('Cannot delete injury with associated recovery plans. Please delete the recovery plans first or use the delete button from the edit page.', 'danger')
        return redirect(url_for('admin.user_injuries', user_id=user_id))
    
    try:
        # If cascade delete is requested, delete all associated recovery plans first
        if recovery_plans and cascade_delete:
            logger.info(f"Performing cascade delete for injury {id} with {len(recovery_plans)} associated recovery plans")
            for plan in recovery_plans:
                # Delete medications and exercises for each plan
                db.session.delete(plan)
            
        # Then delete the injury
        db.session.delete(injury)
        db.session.commit()
        flash('Injury deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting injury: {str(e)}")
        flash('An error occurred while deleting the injury.', 'danger')
    
    return redirect(url_for('admin.user_injuries', user_id=user_id))

@admin.route('/users/new', methods=['GET', 'POST'])
@admin_required
def new_user():
    form = CreateUserForm()
    
    if form.validate_on_submit():
        logger.info("User creation form validated successfully")
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            password=form.password.data,
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!', 'success')
        return redirect(url_for('admin.users'))
    elif request.method == 'POST':
        logger.error(f"User creation form validation failed. Errors: {form.errors}")
    
    return render_template('admin/users/new.html', form=form) 