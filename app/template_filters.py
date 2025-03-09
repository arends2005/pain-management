from flask import Blueprint

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