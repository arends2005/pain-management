#!/usr/bin/env python
import os
import sys
import datetime
import random
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, timedelta

# Set up Flask app to access the application context
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db/pain_management')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Import extensions first
from app.extensions import db

# Initialize the app with the extension
db.init_app(app)

# This function will be called within app context
def simulate_reminders(user_id, days=1, yes_probability=0.8):
    """
    Simulate medication and exercise reminders for a specified number of days
    
    Args:
        user_id: The user ID to simulate reminders for
        days: Number of days to simulate
        yes_probability: Probability (0.0-1.0) of a "YES" response (vs "NO")
    """
    # Import models here to avoid circular dependencies
    from app.models.user import User
    from app.models.injury import Injury
    from app.models.recovery_plan import RecoveryPlan, Medication, Exercise, DiscordInteractionLog, MedicationDose, ExerciseSession
    
    print(f"Simulating reminders for user ID {user_id} over {days} days")
    print(f"Response probability: {yes_probability*100:.0f}% YES, {(1-yes_probability)*100:.0f}% NO")
    
    # Get the user
    user = User.query.get(user_id)
    if not user:
        print(f"User with ID {user_id} not found")
        return
    
    print(f"Found user: {user.username}")
    
    # Check if user has Discord preferences
    if not user.discord_preferences or not user.discord_preferences.discord_channel_id:
        print("User has no Discord preferences or channel ID set")
        return
    
    channel_id = user.discord_preferences.discord_channel_id
    print(f"Discord channel ID: {channel_id}")
    
    # Get active recovery plans
    plans = RecoveryPlan.query.filter_by(user_id=user_id, is_active=True).all()
    if not plans:
        print("No active recovery plans found")
        return
    
    print(f"Found {len(plans)} active recovery plans")
    
    # Current time
    now = datetime.utcnow()
    
    # Simulate over the specified number of days
    for day in range(days):
        day_start = now - timedelta(days=days-day-1)
        day_end = day_start + timedelta(days=1)
        print(f"\nSimulating Day {day+1}: {day_start.date()}")
        
        # Process each plan
        for plan in plans:
            print(f"\nPlan: {plan.name}")
            
            # Get medications with Discord notifications enabled
            medications = Medication.query.filter_by(
                recovery_plan_id=plan.id,
                is_active=True,
                discord_notifications=True
            ).all()
            
            print(f"Found {len(medications)} medications with Discord notifications enabled")
            
            # Simulate medication reminders and responses
            for med in medications:
                print(f"  Medication: {med.name}, Frequency: {med.frequency} hours")
                
                # Calculate how many times this medication should be taken per day
                times_per_day = min(24 // med.frequency, 4)  # Cap at 4 reminders per day for simulation
                
                for i in range(times_per_day):
                    reminder_time = day_start + timedelta(hours=i*med.frequency)
                    
                    # Skip if reminder time is in the future
                    if reminder_time > now:
                        continue
                    
                    # Randomly determine if the medication was taken
                    taken = random.random() < yes_probability
                    response = "YES" if taken else "NO"
                    
                    # Create interaction log (simulating a reminder being sent)
                    message = f"**Medication Reminder**\n\n📋 Plan: {plan.name}\n📋 {med.name}\n💊 Dosage: {med.dosage}\n⏰ Every {med.frequency} hours\n\n{med.instructions if med.instructions else ''}\n\nPlease reply with **YES** if you've taken this medication, or **NO** if you haven't."
                    
                    log = DiscordInteractionLog(
                        user_id=user_id,
                        discord_channel_id=channel_id,
                        message_type='medication',
                        medication_id=med.id,
                        sent_message=message,
                        timestamp=reminder_time,
                        response=response,
                        response_time=reminder_time + timedelta(minutes=5),  # User responded 5 minutes later
                        completed=taken
                    )
                    db.session.add(log)
                    
                    # Create medication dose record
                    dose = MedicationDose(
                        medication_id=med.id,
                        timestamp=reminder_time,
                        taken=taken,
                        response_time=reminder_time + timedelta(minutes=5)
                    )
                    db.session.add(dose)
                    
                    print(f"    Added medication dose at {reminder_time} - Response: {response}")
            
            # Get exercises with Discord notifications enabled
            exercises = Exercise.query.filter_by(
                recovery_plan_id=plan.id,
                is_active=True,
                discord_notifications=True
            ).all()
            
            print(f"Found {len(exercises)} exercises with Discord notifications enabled")
            
            # Simulate exercise reminders and responses
            for ex in exercises:
                print(f"  Exercise: {ex.name}, Frequency: {ex.frequency} hours")
                
                # Calculate how many times this exercise should be done per day
                times_per_day = min(24 // ex.frequency, 2)  # Cap at 2 reminders per day for simulation
                
                for i in range(times_per_day):
                    reminder_time = day_start + timedelta(hours=i*ex.frequency + 2)  # Offset by 2 hours from medications
                    
                    # Skip if reminder time is in the future
                    if reminder_time > now:
                        continue
                    
                    # Randomly determine if the exercise was completed
                    completed = random.random() < yes_probability
                    response = "YES" if completed else "NO"
                    
                    # Create interaction log (simulating a reminder being sent)
                    details = []
                    if ex.duration:
                        details.append(f"⏱️ Duration: {ex.duration}")
                    if ex.repetitions:
                        details.append(f"🔄 Repetitions: {ex.repetitions}")
                    
                    details_str = "\n".join(details) if details else ""
                    
                    message = f"**Exercise Reminder**\n\n📋 Plan: {plan.name}\n🏋️ {ex.name}\n{details_str}\n⏰ Every {ex.frequency} hours\n\n{ex.description if ex.description else ''}\n\n{ex.instructions if ex.instructions else ''}\n\nPlease reply with **YES** if you've completed this exercise, or **NO** if you haven't."
                    
                    log = DiscordInteractionLog(
                        user_id=user_id,
                        discord_channel_id=channel_id,
                        message_type='exercise',
                        exercise_id=ex.id,
                        sent_message=message,
                        timestamp=reminder_time,
                        response=response,
                        response_time=reminder_time + timedelta(minutes=10),  # User responded 10 minutes later
                        completed=completed
                    )
                    db.session.add(log)
                    
                    # Create exercise session record
                    session = ExerciseSession(
                        exercise_id=ex.id,
                        timestamp=reminder_time,
                        completed=completed,
                        response_time=reminder_time + timedelta(minutes=10)
                    )
                    db.session.add(session)
                    
                    # Add difficulty if exercise was completed
                    if completed:
                        session.difficulty = random.randint(3, 8)  # Random difficulty between 3-8
                    
                    print(f"    Added exercise session at {reminder_time} - Response: {response}")
    
    # Commit all changes
    db.session.commit()
    print("\nSimulation completed successfully")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_discord_reminders.py <user_id> [days] [yes_probability]")
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    days = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    yes_probability = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
    
    # Initialize the app context
    with app.app_context():
        simulate_reminders(user_id, days, yes_probability) 