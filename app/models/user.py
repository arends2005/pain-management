from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.extensions import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    phone_number = db.Column(db.String(20), nullable=True)
    profile_picture = db.Column(db.String(120), nullable=True, default='default.jpg')
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    injuries = db.relationship('Injury', backref='user', lazy=True, cascade='all, delete-orphan')
    recovery_plans = db.relationship('RecoveryPlan', backref='user', lazy=True, cascade='all, delete-orphan')
    text_preferences = db.relationship('TextPreference', backref='user', uselist=False, cascade='all, delete-orphan')
    
    @property
    def password(self):
        raise AttributeError('Password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

    @classmethod
    def get_users_count(cls):
        """Return the count of non-admin users"""
        return cls.query.filter_by(is_admin=False).count()

class TextPreference(db.Model):
    __tablename__ = 'text_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    enabled = db.Column(db.Boolean, default=True)
    daily_limit = db.Column(db.Integer, default=5)
    quiet_hours_start = db.Column(db.Time, nullable=True)
    quiet_hours_end = db.Column(db.Time, nullable=True)
    time_zone = db.Column(db.String(50), default='UTC')
    receive_reminders = db.Column(db.Boolean, default=True)
    reminder_time = db.Column(db.Time, nullable=True)
    reminder_frequency = db.Column(db.String(20), default='daily')
    receive_progress_updates = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<TextPreference for User {self.user_id}>' 