import requests
import sys
from urllib.parse import urljoin

BASE_URL = 'http://localhost:5000'

def get_csrf_token(session, url):
    response = session.get(url)
    # Very basic extraction of CSRF token
    if 'csrf_token' in response.text:
        start = response.text.find('name="csrf_token" value="') + len('name="csrf_token" value="')
        end = response.text.find('"', start)
        return response.text[start:end]
    return None

def login(username='admin@admin.com', password='admin'):
    session = requests.Session()
    login_url = urljoin(BASE_URL, '/auth/login')
    
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
    response = session.post(login_url, data=login_data, allow_redirects=True)
    
    # Check if login was successful
    if response.url == urljoin(BASE_URL, '/'):
        print("Login successful")
    else:
        print(f"Login failed, redirected to {response.url}")
        return None
    
    # Try to access dashboard
    dashboard_url = urljoin(BASE_URL, '/user/dashboard')
    response = session.get(dashboard_url)
    
    print(f"Dashboard status code: {response.status_code}")
    if response.status_code == 200:
        print("Dashboard accessed successfully")
    else:
        print("Failed to access dashboard")
    
    return session

if __name__ == "__main__":
    login() 