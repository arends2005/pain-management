from datetime import datetime, time, date
from app.extensions import db

class RecoveryPlan(db.Model):
    __tablename__ = 'recovery_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    injury_id = db.Column(db.Integer, db.ForeignKey('injuries.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    medications = db.relationship('Medication', backref='recovery_plan', lazy=True, cascade='all, delete-orphan')
    exercises = db.relationship('Exercise', backref='recovery_plan', lazy=True, cascade='all, delete-orphan')
    reminders = db.relationship('Reminder', backref='recovery_plan', lazy=True, cascade='all, delete-orphan')
    
    @property
    def progress(self):
        """Calculate recovery plan progress based on time elapsed or completed sessions"""
        if not self.is_active:
            return 100
            
        if not self.end_date:
            # If no end date, estimate based on activity completion rate
            med_doses = sum(len(med.doses) for med in self.medications if med.is_active)
            ex_sessions = sum(len(ex.sessions) for ex in self.exercises if ex.is_active)
            total_activities = max(1, len(self.medications) + len(self.exercises))
            
            # Simplified calculation for now
            return min(95, (med_doses + ex_sessions) * 5)
        
        # Calculate progress based on time elapsed
        today = date.today()
        total_days = (self.end_date - self.start_date).days
        if total_days <= 0:
            return 50  # Default value if dates are invalid
            
        days_elapsed = (today - self.start_date).days
        progress = min(95, max(5, int((days_elapsed / total_days) * 100)))
        return progress
    
    def __repr__(self):
        return f'<RecoveryPlan {self.name} for User {self.user_id}>'

class Medication(db.Model):
    __tablename__ = 'medications'
    
    id = db.Column(db.Integer, primary_key=True)
    recovery_plan_id = db.Column(db.Integer, db.ForeignKey('recovery_plans.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50), nullable=False)
    frequency = db.Column(db.Integer, nullable=False)  # Hours between doses
    instructions = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    discord_notifications = db.Column(db.Boolean, default=False)
    
    # Relationships
    doses = db.relationship('MedicationDose', backref='medication', lazy=True, cascade='all, delete-orphan')
    reminders = db.relationship('Reminder', backref='medication', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Medication {self.name} for Plan {self.recovery_plan_id}>'

class Exercise(db.Model):
    __tablename__ = 'exercises'
    
    id = db.Column(db.Integer, primary_key=True)
    recovery_plan_id = db.Column(db.Integer, db.ForeignKey('recovery_plans.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    frequency = db.Column(db.Integer, nullable=False)  # Hours between exercise sessions
    duration = db.Column(db.String(50), nullable=True)  # e.g., '15 minutes'
    repetitions = db.Column(db.String(50), nullable=True)  # e.g., '3 sets of 10'
    instructions = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    discord_notifications = db.Column(db.Boolean, default=False)
    
    # Relationships
    sessions = db.relationship('ExerciseSession', backref='exercise', lazy=True, cascade='all, delete-orphan')
    reminders = db.relationship('Reminder', backref='exercise', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Exercise {self.name} for Plan {self.recovery_plan_id}>'

class MedicationDose(db.Model):
    __tablename__ = 'medication_doses'
    
    id = db.Column(db.Integer, primary_key=True)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    taken = db.Column(db.Boolean, default=False)
    response_time = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __repr__(self):
        return f'<MedicationDose for Medication {self.medication_id} at {self.timestamp}>'

class ExerciseSession(db.Model):
    __tablename__ = 'exercise_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)
    response_time = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    difficulty = db.Column(db.Integer, nullable=True)  # Scale of 1-10
    
    def __repr__(self):
        return f'<ExerciseSession for Exercise {self.exercise_id} at {self.timestamp}>'

class Reminder(db.Model):
    __tablename__ = 'reminders'
    
    id = db.Column(db.Integer, primary_key=True)
    recovery_plan_id = db.Column(db.Integer, db.ForeignKey('recovery_plans.id'), nullable=False)
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=True)
    time = db.Column(db.Time, nullable=False)
    days = db.Column(db.String(50), nullable=False)  # e.g., 'Mon,Wed,Fri'
    message = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_sent = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        if self.medication_id:
            return f'<Reminder for Medication {self.medication_id} at {self.time}>'
        elif self.exercise_id:
            return f'<Reminder for Exercise {self.exercise_id} at {self.time}>'
        else:
            return f'<Reminder for Plan {self.recovery_plan_id} at {self.time}>'

class DiscordInteractionLog(db.Model):
    __tablename__ = 'discord_interaction_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    discord_channel_id = db.Column(db.String(50), nullable=False)  # Store the channel ID used for the interaction
    message_type = db.Column(db.String(20), nullable=False)  # 'medication', 'exercise', 'test'
    medication_id = db.Column(db.Integer, db.ForeignKey('medications.id'), nullable=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    sent_message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=True)
    response_time = db.Column(db.DateTime, nullable=True)
    completed = db.Column(db.Boolean, default=False)
    discord_message_id = db.Column(db.String(50), nullable=True)  # Store Discord message ID for reference
    
    # Relationships
    user = db.relationship('User', backref='discord_logs')
    medication = db.relationship('Medication', backref='discord_logs')
    exercise = db.relationship('Exercise', backref='discord_logs')
    
    def __repr__(self):
        return f'<DiscordInteractionLog {self.id} - {self.message_type}>' 