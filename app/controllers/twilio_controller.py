import os
from datetime import datetime
from flask import Blueprint, request, jsonify
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from app.extensions import db
from app.models.user import User
from app.models.recovery_plan import Medication, Exercise, MedicationDose, ExerciseSession, RecoveryPlan

twilio = Blueprint('twilio', __name__)

# Initialize Twilio client
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
client = Client(account_sid, auth_token) if account_sid and auth_token else None

@twilio.route('/send-reminder', methods=['POST'])
def send_reminder():
    """API endpoint to send a reminder message"""
    phone_number = request.json.get('phone_number')
    message_body = request.json.get('message')
    reminder_type = request.json.get('type')  # 'medication' or 'exercise'
    reminder_id = request.json.get('id')  # id of the medication or exercise
    
    if not all([phone_number, message_body, reminder_type, reminder_id]):
        return jsonify({'error': 'Missing required parameters'}), 400
    
    if not client:
        return jsonify({'error': 'Twilio not configured'}), 500
    
    try:
        message = client.messages.create(
            body=message_body,
            from_=twilio_phone,
            to=phone_number
        )
        
        # Store information that a message was sent
        if reminder_type == 'medication':
            medication = Medication.query.get(reminder_id)
            if medication:
                dose = MedicationDose(
                    medication_id=reminder_id,
                    timestamp=datetime.utcnow(),
                    taken=False
                )
                db.session.add(dose)
                db.session.commit()
        
        elif reminder_type == 'exercise':
            exercise = Exercise.query.get(reminder_id)
            if exercise:
                session = ExerciseSession(
                    exercise_id=reminder_id,
                    timestamp=datetime.utcnow(),
                    completed=False
                )
                db.session.add(session)
                db.session.commit()
        
        return jsonify({
            'success': True,
            'message_sid': message.sid
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@twilio.route('/webhook', methods=['POST'])
def webhook():
    """Webhook to receive SMS responses"""
    # Get the incoming message
    from_number = request.values.get('From', '')
    body = request.values.get('Body', '').strip().upper()
    
    # Create a response object
    resp = MessagingResponse()
    
    # Find the user by phone number
    user = User.query.filter_by(phone_number=from_number).first()
    if not user:
        resp.message("Sorry, we couldn't find your account. Please contact support.")
        return str(resp)
    
    # Process the response (YES/NO)
    if body in ['YES', 'Y']:
        # Find the most recent unanswered reminder
        med_dose = MedicationDose.query.join(Medication).join(RecoveryPlan).filter(
            RecoveryPlan.user_id == user.id,
            MedicationDose.taken == False,
            MedicationDose.response_time == None
        ).order_by(MedicationDose.timestamp.desc()).first()
        
        if med_dose:
            med_dose.taken = True
            med_dose.response_time = datetime.utcnow()
            db.session.commit()
            medication = Medication.query.get(med_dose.medication_id)
            resp.message(f"Great! We've recorded that you've taken your {medication.name}.")
            return str(resp)
        
        exercise = ExerciseSession.query.join(Exercise).join(RecoveryPlan).filter(
            RecoveryPlan.user_id == user.id,
            ExerciseSession.completed == False,
            ExerciseSession.response_time == None
        ).order_by(ExerciseSession.timestamp.desc()).first()
        
        if exercise:
            exercise.completed = True
            exercise.response_time = datetime.utcnow()
            db.session.commit()
            exercise_info = Exercise.query.get(exercise.exercise_id)
            resp.message(f"Great! We've recorded that you've completed your {exercise_info.name}.")
            return str(resp)
        
        resp.message("Thank you for your response, but we couldn't find a pending reminder.")
    
    elif body in ['NO', 'N']:
        # Similar logic for "NO" responses
        med_dose = MedicationDose.query.join(Medication).join(RecoveryPlan).filter(
            RecoveryPlan.user_id == user.id,
            MedicationDose.taken == False,
            MedicationDose.response_time == None
        ).order_by(MedicationDose.timestamp.desc()).first()
        
        if med_dose:
            med_dose.taken = False
            med_dose.response_time = datetime.utcnow()
            db.session.commit()
            medication = Medication.query.get(med_dose.medication_id)
            resp.message(f"We've recorded that you haven't taken your {medication.name}. Remember to take it as prescribed.")
            return str(resp)
        
        exercise = ExerciseSession.query.join(Exercise).join(RecoveryPlan).filter(
            RecoveryPlan.user_id == user.id,
            ExerciseSession.completed == False,
            ExerciseSession.response_time == None
        ).order_by(ExerciseSession.timestamp.desc()).first()
        
        if exercise:
            exercise.completed = False
            exercise.response_time = datetime.utcnow()
            db.session.commit()
            exercise_info = Exercise.query.get(exercise.exercise_id)
            resp.message(f"We've recorded that you haven't completed your {exercise_info.name}. Remember that consistent exercise helps recovery.")
            return str(resp)
        
        resp.message("Thank you for your response, but we couldn't find a pending reminder.")
    
    else:
        resp.message("Please respond with YES or NO.")
    
    return str(resp)

@twilio.route('/check-scheduled-reminders')
def check_scheduled_reminders():
    """
    Check for reminders that need to be sent now
    This would be called by a scheduler (e.g., cron job)
    """
    # Implementation would check the database for reminders that need to be sent
    # based on their schedule and then call the send_reminder function
    return jsonify({'status': 'check_scheduled_reminders endpoint is ready'}) 