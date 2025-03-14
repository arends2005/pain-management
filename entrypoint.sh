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
echo "Ensuring database tables exist and are up to date..."
python db_init_with_upgrades.py

# Start the main application
echo "Starting Flask application..."
exec "$@" 