import os
import sys
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify, g
import logging
from config import Config
from app.utils.logging_helper import setup_app_logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app(config_class=Config):
    # Initialize Flask app
    app = Flask(__name__, 
                template_folder='app/templates',
                static_folder='app/static')
    
    # Configure app from Config class
    app.config.from_object(config_class)
    
    # Set up enhanced logging
    setup_app_logging(app)
    
    # Initialize extensions
    from app.extensions import db, migrate, login_manager
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Register custom template filters
    from app.template_filters import template_filters
    app.register_blueprint(template_filters)
    
    with app.app_context():
        # Import models - after db is initialized
        from app.models.user import User
        from app.models.injury import Injury
        from app.models.recovery_plan import RecoveryPlan, Medication, Exercise
        
        # Import blueprints - after models are imported
        from app.controllers.auth_controller import auth
        from app.controllers.user_controller import user
        from app.controllers.admin_controller import admin
        from app.controllers.twilio_controller import twilio
        
        # Register blueprints
        app.register_blueprint(auth, url_prefix='/auth')
        app.register_blueprint(user, url_prefix='/user')
        app.register_blueprint(admin, url_prefix='/admin')
        app.register_blueprint(twilio, url_prefix='/twilio')
        
        # Add context processor for current date/time
        @app.context_processor
        def inject_now():
            return {'now': datetime.now()}
        
        @login_manager.user_loader
        def load_user(user_id):
            # Update to use session.get() to fix SQLAlchemy warning
            return db.session.get(User, int(user_id))
        
        # Set user_id in Flask g object for logging purposes
        @app.before_request
        def before_request():
            from flask_login import current_user
            if current_user.is_authenticated:
                g.user_id = current_user.id
            else:
                g.user_id = None
        
        @app.route('/')
        def index():
            from flask_login import current_user
            if current_user.is_authenticated:
                if current_user.is_admin:
                    return redirect(url_for('admin.dashboard'))
                return redirect(url_for('user.dashboard'))
            return render_template('index.html')
        
        @app.errorhandler(404)
        def page_not_found(e):
            return render_template('404.html'), 404
        
        @app.errorhandler(500)
        def server_error(e):
            return render_template('500.html'), 500
        
        # Create admin user if it doesn't exist
        @app.before_first_request
        def create_admin():
            try:
                db.create_all()
                admin_username = app.config['ADMIN_USERNAME']
                admin_email = app.config['ADMIN_EMAIL']
                admin_password = app.config['ADMIN_PASSWORD']
                
                admin_user = User.query.filter_by(email=admin_email).first()
                if not admin_user:
                    admin_user = User(
                        username=admin_username,
                        email=admin_email,
                        password=admin_password,
                        is_admin=True
                    )
                    db.session.add(admin_user)
                    db.session.commit()
                    logger.info(f"Admin user {admin_email} created.")
            except Exception as e:
                logger.error(f"Error creating admin user: {str(e)}")
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 