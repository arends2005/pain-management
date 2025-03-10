#!/bin/bash
# Script to rebuild the Discord bot and database

echo "📦 Rebuilding Discord Bot and Database..."
echo "This will delete all existing data! Press Ctrl+C to cancel."
echo "Waiting 5 seconds..."
sleep 5

echo "🛑 Stopping and removing existing containers..."
docker compose down -v

echo "🏗️ Building new containers..."
docker compose up --build -d

echo "🔄 Waiting for database to initialize..."
sleep 10

echo "🔧 Applying database schema changes..."
docker compose exec web python -c '
import sys
import os
sys.path.insert(0, "/app")
from flask import Flask
from config import Config
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.config.from_object(Config)
from app.extensions import db

# Import all models to ensure they are registered with SQLAlchemy
from app.models.user import User, TextPreference, DiscordPreference, SystemSettings
from app.models.injury import Injury, ProgressLog
from app.models.recovery_plan import RecoveryPlan, Medication, Exercise, DiscordInteractionLog, MedicationDose, ExerciseSession

db.init_app(app)
with app.app_context():
    db.create_all()
    print("Database schema updated successfully!")

    # List all tables to verify
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    print("Tables in database:")
    for table_name in inspector.get_table_names():
        print(f"- {table_name}")
'

echo "✅ Rebuild complete!"
echo ""
echo "To test the Discord bot connection, use:"
echo "docker compose exec web python test_discord_channel.py <channel_id> <bot_token>"
echo ""
echo "Make sure to update your Discord preferences in the app to add a channel ID" 