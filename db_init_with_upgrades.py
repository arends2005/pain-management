import sys
import os
from flask import Flask
from config import Config
from app.extensions import db
from sqlalchemy import text, inspect

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Import all models to ensure they are registered with SQLAlchemy
from app.models.user import User, TextPreference, DiscordPreference, SystemSettings
from app.models.injury import Injury, ProgressLog
from app.models.recovery_plan import RecoveryPlan, Medication, Exercise, DiscordInteractionLog, MedicationDose, ExerciseSession

def ensure_column_exists(table_name, column_name, column_type):
    """Check if a column exists in a table, if not add it"""
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if column_name not in columns:
            print(f"Adding column {column_name} to table {table_name}")
            db.session.execute(text(f"""
            ALTER TABLE {table_name} 
            ADD COLUMN {column_name} {column_type};
            """))
            return True
        else:
            print(f"Column {column_name} already exists in table {table_name}")
            return False
    except Exception as e:
        print(f"Error checking/adding column {column_name} to {table_name}: {e}")
        return False

def main():
    with app.app_context():
        # Create all tables if they don't exist
        db.create_all()
        print("Base database schema created or verified")
        
        # Ensure all required columns exist (add more as needed)
        columns_to_verify = [
            {
                'table': 'discord_interaction_logs', 
                'column': 'scheduled_time', 
                'type': 'TIMESTAMP WITHOUT TIME ZONE'
            },
            # Add more columns here if needed in the future
        ]
        
        changes_made = False
        for col in columns_to_verify:
            if ensure_column_exists(col['table'], col['column'], col['type']):
                changes_made = True
        
        # Update data if any schema changes were made
        if changes_made:
            # Fill in scheduled_time with timestamp for existing records if needed
            db.session.execute(text("""
            UPDATE discord_interaction_logs
            SET scheduled_time = timestamp
            WHERE message_type IN ('medication', 'exercise')
            AND scheduled_time IS NULL;
            """))
        
        db.session.commit()
        
        # List all tables to verify
        inspector = inspect(db.engine)
        print("\nTables in database:")
        for table_name in sorted(inspector.get_table_names()):
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            print(f"- {table_name}: {', '.join(columns)}")
        
        print("\nDatabase initialization and verification complete!")

if __name__ == "__main__":
    main() 