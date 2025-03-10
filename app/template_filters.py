from flask import Blueprint
import pytz
from datetime import datetime, date

template_filters = Blueprint('filters', __name__)

@template_filters.app_template_filter('yesno')
def yesno_filter(value, options='yes,no'):
    """
    Django-style yesno filter for Jinja2.
    Returns one of the options based on the value - first for truthy, second for falsy.
    Example: {{ value|yesno('Enabled,Disabled') }}
    """
    options_list = options.split(',')
    if len(options_list) < 2:
        options_list = ['yes', 'no']
    
    return options_list[0] if value else options_list[1]

@template_filters.app_template_filter('to_pacific')
def to_pacific_time(dt):
    """
    Convert a UTC datetime to Pacific Time.
    If a date object is passed, return it unchanged.
    """
    if not dt:
        return ''
    
    # If it's a date object (not a datetime), return it as is
    if isinstance(dt, date) and not isinstance(dt, datetime):
        return dt
    
    # If the datetime is naive (no timezone info), assume it's UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)
    
    # Convert to Pacific Time
    pacific = pytz.timezone('America/Los_Angeles')
    pacific_dt = dt.astimezone(pacific)
    
    return pacific_dt

@template_filters.app_template_filter('strftime')
def strftime_filter(dt, format='%Y-%m-%d %H:%M:%S'):
    """
    Format a datetime object using strftime.
    Example: {{ some_date|strftime('%Y-%m-%d') }}
    """
    if not dt:
        return ''
    
    if hasattr(dt, 'strftime'):
        return dt.strftime(format)
    
    return str(dt) 