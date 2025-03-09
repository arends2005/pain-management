#!/bin/bash
set -e

echo "Setting up migrations for Pain Management App"

# Check if container is running
if ! docker compose ps | grep -q "web.*running"; then
  echo "Web container is not running. Starting container..."
  docker compose up -d
  
  # Give container time to start
  echo "Waiting for container to start..."
  sleep 5
fi

# Create tables directly using db.create_all()
echo "Ensuring database tables exist..."
docker compose exec web python -c '
import sys
import os
sys.path.insert(0, "/app")
from flask import Flask
from config import Config
app = Flask(__name__, template_folder="app/templates", static_folder="app/static")
app.config.from_object(Config)
from app.extensions import db, migrate
db.init_app(app)
with app.app_context():
    db.create_all()
    print("Database tables created successfully!")
'

echo "Database setup complete!" 