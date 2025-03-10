import requests
import sys
from urllib.parse import urljoin
import re

# Change localhost to the service name where your web app is running
BASE_URL = 'http://localhost:5000'

def get_csrf_token(session, url):
    response = session.get(url)
    print(f"Status code for CSRF page: {response.status_code}")
    
    # Use a proper regex pattern to extract the CSRF token
    csrf_pattern = re.compile(r'name="csrf_token" type="hidden" value="([^"]+)"')
    match = csrf_pattern.search(response.text)
    
    if match:
        token = match.group(1)
        print(f"Found CSRF token: {token}")
        return token
    else:
        print("No CSRF token found in response")
        print("Response HTML snippet:")
        print(response.text[:500])  # Print first 500 chars to see form structure
    return None

def login(username='admin@admin.com', password='admin'):
    session = requests.Session()
    login_url = urljoin(BASE_URL, '/auth/login')
    print(f"Attempting to connect to: {login_url}")
    
    # Get CSRF token
    csrf_token = get_csrf_token(session, login_url)
    if not csrf_token:
        print("Failed to get CSRF token")
        return None
    
    # Login
    login_data = {
        'email': username,
        'password': password,
        'csrf_token': csrf_token,
    }
    print(f"Sending login data: {login_data}")
    response = session.post(login_url, data=login_data, allow_redirects=True)
    print(f"Login response status code: {response.status_code}")
    print(f"Login response headers: {dict(response.headers)}")
    
    # Check if login was successful - update to check for admin dashboard or user dashboard
    if response.url == urljoin(BASE_URL, '/') or '/dashboard' in response.url:
        print("Login successful, redirected to:", response.url)
    else:
        print(f"Login failed, redirected to {response.url}")
        # Print a snippet of the response to see error messages
        print("Response snippet:")
        print(response.text[:500])
        return None
    
    # Try to access dashboard if not already there
    if not '/dashboard' in response.url:
        dashboard_url = urljoin(BASE_URL, '/user/dashboard')
        print(f"Accessing dashboard at: {dashboard_url}")
        response = session.get(dashboard_url)
        
        print(f"Dashboard status code: {response.status_code}")
        if response.status_code == 200:
            print("Dashboard accessed successfully")
        else:
            print("Failed to access dashboard")
    else:
        print("Already on dashboard page")
    
    return session

if __name__ == "__main__":
    login() 