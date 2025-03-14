import sys
import os
sys.path.insert(0, "/app")
from flask import Flask
from config import Config
from app.extensions import db
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    # Add the scheduled_time column if it doesn't exist
    try:
        db.session.execute(text("""
        ALTER TABLE discord_interaction_logs 
        ADD COLUMN IF NOT EXISTS scheduled_time TIMESTAMP WITHOUT TIME ZONE;
        """))
        
        # Update existing records to use timestamp as scheduled_time
        db.session.execute(text("""
        UPDATE discord_interaction_logs
        SET scheduled_time = timestamp
        WHERE message_type IN ('medication', 'exercise')
        AND scheduled_time IS NULL;
        """))
        
        db.session.commit()
        print("Migration completed successfully!")
    except Exception as e:
        print(f"Error during migration: {e}")
        db.session.rollback() 