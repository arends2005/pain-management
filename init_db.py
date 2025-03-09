#!/usr/bin/env python3
"""
Database initialization script for the Pain Management App.
This script creates the necessary database tables and initializes admin user.
"""
import sys
import os

# Ensure app module can be found
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import app
from app.extensions import db
from app.models.user import User, TextPreference

# Get app context
from app import app

def init_db():
    """Initialize the database with required tables and default admin user."""
    with app.app_context():
        # Create tables
        db.create_all()
        
        # Check if admin user exists
        admin_email = app.config['ADMIN_EMAIL']
        admin_user = User.query.filter_by(email=admin_email).first()
        
        if not admin_user:
            # Create admin user
            admin_user = User(
                username=app.config['ADMIN_USERNAME'],
                email=admin_email,
                password=app.config['ADMIN_PASSWORD'],
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user {admin_email} created successfully")
        else:
            print(f"Admin user {admin_email} already exists")
        
        # Ensure admin has text preferences
        if not hasattr(admin_user, 'text_preferences') or admin_user.text_preferences is None:
            text_pref = TextPreference(
                user=admin_user,
                enabled=True
            )
            db.session.add(text_pref)
            db.session.commit()
            print("Text preferences created for admin user")
        else:
            print("Admin user already has text preferences")
            
        print("Database initialization completed successfully")
        return True

if __name__ == "__main__":
    init_db() 