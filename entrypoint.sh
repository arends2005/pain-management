#!/bin/bash
set -e

# Wait for database to be ready
echo "Waiting for database..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "Database is ready!"

# Set Flask app explicitly
export FLASK_APP=app.py

# Ensure upload directories exist with proper permissions
echo "Setting up upload directories with proper permissions..."
mkdir -p /app/app/static/uploads/profile_pics
chmod -R 777 /app/app/static/uploads
echo "Upload directories ready!"

# Ensure database tables exist using create_all
echo "Ensuring database tables exist..."
python -c '
import sys
import os
sys.path.insert(0, "/app")
from flask import Flask
from config import Config
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.config.from_object(Config)
from app.extensions import db, migrate

# Import all models to ensure they are registered with SQLAlchemy
from app.models.user import User, TextPreference, DiscordPreference, SystemSettings
from app.models.injury import Injury, ProgressLog
from app.models.recovery_plan import RecoveryPlan, Medication, Exercise, DiscordInteractionLog, MedicationDose, ExerciseSession

db.init_app(app)
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
    
    # List all tables to verify
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print("Created tables:")
    for table_name in inspector.get_table_names():
        print(f"- {table_name}")
        
    # Verify the text_preferences table has reminder_frequency column
    if "text_preferences" in inspector.get_table_names():
        columns = [column["name"] for column in inspector.get_columns("text_preferences")]
        print(f"Columns in text_preferences: {columns}")
        if "reminder_frequency" in columns:
            print("SUCCESS: reminder_frequency column exists!")
        else:
            print("WARNING: reminder_frequency column is missing!")
'

# Start the main application
echo "Starting Flask application..."
exec "$@" 