#!/usr/bin/env python
import os
import sys
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, timedelta

# Set up Flask app to access the application context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://docker:docker@db/pain_management')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import extensions first
from app.extensions import db

# Initialize the app with the extension
db.init_app(app)

# This function will check for Discord reminders
def check_discord_reminders(user_id):
    """Check if Discord reminders are set up for a user"""
    # Import models here to avoid circular dependencies
    from app.models.user import User
    from app.models.recovery_plan import RecoveryPlan, Medication, Exercise
    
    print(f"Checking Discord reminders for user ID {user_id}")
    
    # Get the user
    user = User.query.get(user_id)
    if not user:
        print(f"User with ID {user_id} not found")
        return
    
    print(f"Found user: {user.username}")
    
    # Check if user has Discord preferences
    if not user.discord_preferences:
        print("User has no Discord preferences set up")
    elif not user.discord_preferences.discord_channel_id:
        print("User has Discord preferences but no channel ID set")
    else:
        channel_id = user.discord_preferences.discord_channel_id
        print(f"Discord channel ID: {channel_id}")
    
    # Get active recovery plans
    plans = RecoveryPlan.query.filter_by(user_id=user_id, is_active=True).all()
    print(f"Found {len(plans)} active recovery plans")
    
    if not plans:
        print("No active recovery plans found")
        return
    
    # Process each plan
    for plan in plans:
        print(f"\nPlan: {plan.name} (ID: {plan.id})")
        
        # Get medications with Discord notifications enabled
        medications = Medication.query.filter_by(
            recovery_plan_id=plan.id,
            is_active=True,
            discord_notifications=True
        ).all()
        
        print(f"Found {len(medications)} medications with Discord notifications enabled:")
        for med in medications:
            print(f"  - {med.name} (ID: {med.id}), Frequency: {med.frequency} hours")
        
        # Get exercises with Discord notifications enabled
        exercises = Exercise.query.filter_by(
            recovery_plan_id=plan.id,
            is_active=True,
            discord_notifications=True
        ).all()
        
        print(f"Found {len(exercises)} exercises with Discord notifications enabled:")
        for ex in exercises:
            print(f"  - {ex.name} (ID: {ex.id}), Frequency: {ex.frequency} hours")

if __name__ == "__main__":
    user_id = 2
    if len(sys.argv) > 1:
        user_id = int(sys.argv[1])
    
    # Initialize the app context
    with app.app_context():
        check_discord_reminders(user_id) 