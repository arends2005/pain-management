import logging
import os
import json
from datetime import datetime
from logging.handlers import RotatingFileHandler
from flask import current_app, request, g

# Create logs directory if it doesn't exist
def ensure_log_directory():
    log_dir = os.path.join(os.getcwd(), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    return log_dir

# Setup basic application logging
def setup_app_logging(app):
    log_dir = ensure_log_directory()
    log_level = logging.DEBUG if app.debug else logging.INFO
    
    # General application log
    app_log_file = os.path.join(log_dir, 'app.log')
    app_handler = RotatingFileHandler(app_log_file, maxBytes=10485760, backupCount=10)
    app_handler.setLevel(log_level)
    app_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    
    # Twilio specific log
    twilio_log_file = os.path.join(log_dir, 'twilio.log')
    twilio_handler = RotatingFileHandler(twilio_log_file, maxBytes=10485760, backupCount=10)
    twilio_handler.setLevel(logging.DEBUG)  # Always log Twilio events in detail
    twilio_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    
    # Configure Flask app logger
    app.logger.setLevel(log_level)
    app.logger.addHandler(app_handler)
    
    # Create a separate Twilio logger
    twilio_logger = logging.getLogger('twilio')
    twilio_logger.setLevel(logging.DEBUG)
    twilio_logger.addHandler(twilio_handler)
    
    return app

# Twilio specific logging
class TwilioLogger:
    @staticmethod
    def log_request(phone_number, message, config):
        """Log a Twilio request attempt"""
        logger = logging.getLogger('twilio')
        
        # Sanitize phone number for privacy
        sanitized_phone = phone_number[-4:].rjust(len(phone_number), '*')
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'REQUEST',
            'phone': sanitized_phone,
            'message_length': len(message),
            'config_status': {
                'account_sid': bool(config.get('account_sid')),
                'auth_token': bool(config.get('auth_token')),
                'phone_number': bool(config.get('phone_number'))
            },
            'user_id': g.get('user_id') if hasattr(g, 'user_id') else None
        }
        
        logger.info(f"TWILIO REQUEST: {json.dumps(log_entry)}")
        return log_entry
    
    @staticmethod
    def log_success(phone_number, message_sid, response_data=None):
        """Log a successful Twilio request"""
        logger = logging.getLogger('twilio')
        
        # Sanitize phone number for privacy
        sanitized_phone = phone_number[-4:].rjust(len(phone_number), '*')
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'SUCCESS',
            'phone': sanitized_phone,
            'message_sid': message_sid,
            'response': response_data,
            'user_id': g.get('user_id') if hasattr(g, 'user_id') else None
        }
        
        logger.info(f"TWILIO SUCCESS: {json.dumps(log_entry)}")
        return log_entry
    
    @staticmethod
    def log_error(phone_number, error, error_code=None, config=None):
        """Log a Twilio error"""
        logger = logging.getLogger('twilio')
        
        # Sanitize phone number for privacy (if provided)
        sanitized_phone = None
        if phone_number:
            sanitized_phone = phone_number[-4:].rjust(len(phone_number), '*')
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': 'ERROR',
            'phone': sanitized_phone,
            'error_message': str(error),
            'error_code': error_code,
            'user_id': g.get('user_id') if hasattr(g, 'user_id') else None
        }
        
        # Add configuration status if provided
        if config:
            log_entry['config_status'] = {
                'account_sid': bool(config.get('account_sid')),
                'auth_token': bool(config.get('auth_token')),
                'phone_number': bool(config.get('phone_number'))
            }
        
        logger.error(f"TWILIO ERROR: {json.dumps(log_entry)}")
        return log_entry
    
    @staticmethod
    def get_recent_logs(limit=100):
        """Get recent Twilio logs"""
        log_dir = ensure_log_directory()
        twilio_log_file = os.path.join(log_dir, 'twilio.log')
        logs = []
        
        if os.path.exists(twilio_log_file):
            with open(twilio_log_file, 'r') as file:
                # Read from the end of the file to get the most recent logs
                lines = file.readlines()
                for line in lines[-limit:]:
                    # Parse the log line to extract the JSON part
                    try:
                        # Typical format: '2024-03-09 12:34:56,789 INFO: TWILIO REQUEST: {"event": "REQUEST", ...}'
                        json_start = line.find('{')
                        if json_start != -1:
                            json_data = json.loads(line[json_start:])
                            # Add the type of event (from the log line)
                            if 'REQUEST' in line:
                                json_data['log_type'] = 'REQUEST'
                            elif 'SUCCESS' in line:
                                json_data['log_type'] = 'SUCCESS'
                            elif 'ERROR' in line:
                                json_data['log_type'] = 'ERROR'
                            logs.append(json_data)
                    except Exception as e:
                        # If we can't parse the line, add it as raw text
                        logs.append({'raw_log': line.strip(), 'error': str(e)})
        
        return logs 