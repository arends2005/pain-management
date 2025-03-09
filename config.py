import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check critical environment variables
required_vars = ['DATABASE_URL', 'SESSION_SECRET']
missing_vars = [var for var in required_vars if not os.environ.get(var)]
if missing_vars:
    print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
    print("Please update your .env file with these values before starting the application.")
    if 'pytest' not in sys.modules:  # Don't exit if running tests
        sys.exit(1)

class Config:
    """Base configuration."""
    # Use a development key ONLY for local development, never in production
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Twilio configuration
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Discord configuration
    DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
    DISCORD_APPLICATION_ID = os.environ.get('DISCORD_APPLICATION_ID')
    DISCORD_PUBLIC_KEY = os.environ.get('DISCORD_PUBLIC_KEY')
    DISCORD_BOT_PERMISSIONS = os.environ.get('DISCORD_BOT_PERMISSIONS')
    DISCORD_INVITE_URL = os.environ.get('DISCORD_INVITE_URL')
    
    # App configuration
    INVITE_CODE = os.environ.get('INVITE_CODE')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    
    # For development only - use of these default values in production is a security risk
    if os.environ.get('FLASK_ENV') == 'development':
        if not SECRET_KEY:
            SECRET_KEY = 'dev-key-for-development-only'
            print("WARNING: Using default SECRET_KEY for development")
        if not INVITE_CODE:
            INVITE_CODE = 'zebrano'
            print("WARNING: Using default INVITE_CODE for development")
        if not ADMIN_USERNAME:
            ADMIN_USERNAME = 'admin'
            print("WARNING: Using default ADMIN_USERNAME for development")
        if not ADMIN_EMAIL:
            ADMIN_EMAIL = 'admin@example.com'
            print("WARNING: Using default ADMIN_EMAIL for development")
        if not ADMIN_PASSWORD:
            ADMIN_PASSWORD = 'admin'
            print("WARNING: Using default ADMIN_PASSWORD for development - CHANGE THIS IN PRODUCTION!") 