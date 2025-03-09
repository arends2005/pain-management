from datetime import datetime
from app.extensions import db

class Injury(db.Model):
    __tablename__ = 'injuries'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    severity = db.Column(db.String(20), nullable=False)  # Mild, Moderate, Severe
    injury_type = db.Column(db.String(20), nullable=False)  # Acute, Chronic
    body_location = db.Column(db.String(50), nullable=False)
    date_of_injury = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    recovery_plans = db.relationship('RecoveryPlan', backref='injury', lazy=True, cascade='all, delete-orphan')
    progress_logs = db.relationship('ProgressLog', backref='injury', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Injury {self.name} for User {self.user_id}>'

class ProgressLog(db.Model):
    __tablename__ = 'progress_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    injury_id = db.Column(db.Integer, db.ForeignKey('injuries.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    pain_level = db.Column(db.Integer, nullable=False)  # Scale of 1-10
    notes = db.Column(db.Text, nullable=True)
    mobility = db.Column(db.Integer, nullable=True)  # Percentage (0-100)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProgressLog for Injury {self.injury_id} on {self.date}>' 