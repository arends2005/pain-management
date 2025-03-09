
---

# Help me create a detailed prompt for a pain management app with texting ability and nice charts to visualize the patients recovery.

# You are an amazing full stack developer.

# You are working with a doctor to collect the proper information from the user and help create a detailed recovery plan.

When recovering from an injury, several key categories of information are crucial for understanding and managing the recovery process. Here are some of the most relevant categories:

1. **Type of Injury**:
    - **Acute vs. Chronic**: Acute injuries occur suddenly (e.g., sprains, fractures), while chronic injuries develop over time (e.g., tendinitis, stress fractures).
    - **Severity**: Injuries can range from mild (Grade 1) to severe (Grade 3), impacting recovery time.
2. **Recovery Time**:
    - **Mild Injuries**: Minor sprains or strains may recover in a week or so.
    - **Moderate Injuries**: Partial tears or moderate sprains can take several weeks to months.
    - **Severe Injuries**: Complete tears or fractures may require months for full recovery.
3. **Stages of Rehabilitation**:
    - **Acute/Immediate Care**: Focuses on controlling pain and swelling.
    - **Subacute/Recovery Stage**: Involves restoring range of motion and strength.
    - **Rehabilitation/Strengthening Stage**: Aims to improve strength and function.
    - **Return to Activity**: Gradually reintroduces sport-specific activities.
4. **Treatment and Management**:
    - **RICE Protocol**: Rest, Ice, Compression, Elevation for acute injuries.
    - **Physical Therapy**: Essential for improving strength, flexibility, and function.
    - **Pain Management**: May include medication, massage, or other therapies.
5. **Indicators of Recovery**:
    - **Returning to Normal Activities**: Resuming work, family roles, and achieving independence.
    - **Pain Reduction**: Decrease in pain levels over time.
    - **Functional Improvement**: Enhanced strength, flexibility, and mobility.

# Technical Requirements:

- use Postgresql for the database
- use a .env file
- set default admin in .env file ADMIN_USER=admin, ADMIN_EMAIL=admin@admin.com, ADMIN_PASSWORD=admin
- use twillio for automated text messages
- use docker
- use Dockerfile
- use docker-compose.yml
- use Bootstrap
- have a project structure file

The app should have the following features and components:

### Registration

1. Allow user to create an account and Require INVITE_CODE from .env file for initial registration. 

### User Interface

1. Home page with options to:
    - Edit users profile: name, phone number, email, password reset, profile picture, etc.
    - Add/Edit automated text message preferences
    - Add/Edit injuries
    - Add/Edit recovery plan (Take medication, do stretching, etc.)
    - View recovery plan and charts (plan says how much medication to take and when to take it)
2. Text Interface
    - User gets a text it's time to take your medication, (2 ibuprofen) for example
    - User gets instructions to reply with YES or NO to indicate if they took medication or performed a task required
    - App records answer in database and sets new timer for reminder of next text based medication event

### Admin Interface

1. Admin page with options to:
    - Edit users profile: name, phone number, email, password reset, profile picture, etc.
    - Add/Edit users automated text message preferences
    - Add/Edit users injuries
    - Add/Edit users recovery plan (Take medication, do stretching, etc.)
    - View users recovery plan and charts (plan says how much medication to take and when to take it)

### Functionality

1. Data Management:
    - CRUD operations for user information, automated messages, recovery plan, and injuries
    - CRUD operations for admin
    - Secure storage of recovery plan and results and responses

### Technical Requirements

1. Backend:
    - Use a suitable web framework (e.g., Ruby on Rails, Django, Flask, or Express.js)
    - Implement RESTful API endpoints for data operations
    - Twilio API
2. Database:
    - Use PostgreSQL for data storage
    - Design schema to store user profiles, resultsm etc
3. Frontend:
    - Use Bootstrap for responsive design and make it ios friendly
    - Implement dynamic form rendering
4. DevOps:
    - Use a .env file for environment variables
    - Create a Dockerfile for containerization
    - Implement docker-compose.yml for easy deployment
5. Security:
    - Implement user authentication and authorization
    - Ensure data privacy and protection
6. Code Structure:
    - Follow MVC or similar architectural pattern
    - Create a clear folder structure for different components
    - Implement modular code design for reusability

### Additional Considerations

1. Scalability: Design the app to handle multiple users and multiplel injuries
2. User Experience: Create an intuitive and engaging interface for adding injuries and treatment plans
3. Data Visualization: Implement charts or graphs to display results
4. Customization: Allow users to adjust recovery plans
5. Privacy: Implement features to control visibility of profile information and results
6. Admin: Implement an admin dashboard to allow an admin to adjust user information

Here's a detailed prompt for creating a pain management app with texting ability and visualization features:

---

## Project Overview

Develop a comprehensive pain management app that allows users to track their recovery from injuries. The app should provide features for user registration, profile management, injury tracking, recovery planning, and automated text reminders. It will utilize PostgreSQL for data storage, Twilio for automated text messaging, and Docker for deployment.

## Technical Requirements

- **Database**: PostgreSQL
- **Environment Variables**: Use a `.env` file with default admin credentials set as `ADMIN_USER=admin`, `ADMIN_EMAIL=admin@admin.com`, and `ADMIN_PASSWORD=admin`.
- **Text Messaging**: Integrate Twilio for automated text messages.
- **Deployment**: Use Docker with a `Dockerfile` and `docker-compose.yml`.
- **Frontend**: Implement Bootstrap for responsive design.
- **Project Structure**: Follow an MVC pattern with a clear folder structure.


## Features and Components

### Registration

1. **User Account Creation**: Allow users to create accounts with basic information (name, email, phone number, password).
    - Require INVITE_CODE from .env file for initial registration 

### User Interface

1. **Home Page**:
    - **Edit Profile**: Allow users to update their name, phone number, email, password, and profile picture.
    - **Text Message Preferences**: Users can add or edit preferences for automated text messages.
    - **Injury Management**: Users can add or edit injuries.
    - **Recovery Plan Management**: Users can create or edit recovery plans (e.g., medication schedules, exercises).
    - **Recovery Plan Visualization**: Display recovery plans with charts or graphs showing progress.
2. **Text Interface**:
    - **Medication Reminders**: Send automated text messages reminding users to take medication.
    - **Task Reminders**: Send reminders for exercises or other recovery tasks.
    - **User Feedback**: Users can respond with "YES" or "NO" to confirm completion of tasks.
    - **Database Update**: Record user responses in the database and schedule the next reminder.

### Admin Interface

1. **Admin Dashboard**:
    - **User Profile Management**: Admins can edit user profiles.
    - **Text Message Preferences Management**: Admins can manage users' text message preferences.
    - **Injury Management**: Admins can add or edit users' injuries.
    - **Recovery Plan Management**: Admins can create or edit recovery plans for users.
    - **Recovery Plan Visualization**: Admins can view users' recovery plans with charts or graphs.

### Functionality

1. **Data Management**:
    - **CRUD Operations**: Implement create, read, update, and delete operations for user information, automated messages, recovery plans, and injuries.
    - **Secure Data Storage**: Ensure secure storage of recovery plans and user responses.
2. **Backend**:
    - **Web Framework**: Use a suitable framework like Flask or Django.
    - **RESTful API**: Implement API endpoints for data operations.
    - **Twilio Integration**: Use Twilio API for automated text messaging.
3. **Frontend**:
    - **Responsive Design**: Use Bootstrap for a responsive and iOS-friendly interface.
    - **Dynamic Forms**: Implement dynamic form rendering for user input.
4. **DevOps**:
    - **Environment Variables**: Use a `.env` file for environment variables.
    - **Containerization**: Create a `Dockerfile` for containerization.
    - **Deployment**: Implement `docker-compose.yml` for easy deployment.
5. **Security**:
    - **Authentication and Authorization**: Implement user authentication and authorization.
    - **Data Privacy**: Ensure data privacy and protection.
6. **Code Structure**:
    - **MVC Pattern**: Follow an MVC or similar architectural pattern.
    - **Modular Design**: Implement modular code design for reusability.

### Additional Considerations

1. **Scalability**: Design the app to handle multiple users and injuries.
2. **User Experience**: Create an intuitive interface for adding injuries and treatment plans.
3. **Data Visualization**: Implement charts or graphs to display recovery progress.
4. **Customization**: Allow users to adjust recovery plans.
5. **Privacy**: Implement features to control visibility of profile information and results.
6. **Admin Dashboard**: Provide an admin dashboard for managing user information and recovery plans.

---

## Project Structure

```plaintext
project/
|---- app/
|       |---- models/
|       |       |---- user.py
|       |       |---- injury.py
|       |       |---- recovery_plan.py
|       |---- views/
|       |       |---- user_views.py
|       |       |---- admin_views.py
|       |---- controllers/
|       |       |---- user_controller.py
|       |       |---- admin_controller.py
|       |---- templates/
|       |       |---- user_templates/
|       |       |---- admin_templates/
|       |---- static/
|       |       |---- css/
|       |       |---- js/
|---- config/
|       |---- settings.py
|       |---- database.py
|---- requirements.txt
|---- .env
|---- Dockerfile
|---- docker-compose.yml
|---- README.md
```


## Example Code Snippets

### Dockerfile

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Run app.py when the container launches
CMD ["python", "app.py"]
```


### docker-compose.yml

```yaml
services:
  web:
    build: .
    ports:
      - "3000:3000" # "3020:3000" # Changed host port to 3020 because 3000 was already being used by another container on NGINX Proxy Manager
    volumes:
      - ./src:/usr/src/app/src
    env_file:
      - .env
    environment:
      
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped

  db:
    image: postgres:latest
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5435:5432" # Changed host port to 5435
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```


### .env

```makefile
# Admin account
ADMIN_USERNAME=admin
ADMIN_EMAIL=admin@admin.com
ADMIN_PASSWORD=admin
# Twilio Credentials
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=your_phone_number
# Database Configuration
DATABASE_URL=postgres://docker:docker@db:5432/news_articles
POSTGRES_USER=docker
POSTGRES_PASSWORD=docker
POSTGRES_DB=pain_management
POSTGRES_HOST=db
POSTGRES_PORT=5432
# Application Configuration
NODE_ENV=development
SESSION_SECRET=your_session_secret
INVITE_CODE=zebrano
```


### Example Backend Code (Flask)

```python
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from twilio.rest import Client

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@db:5432/database'
db = SQLAlchemy(app)

# Twilio Client
client = Client('your_account_sid', 'your_auth_token')

# Example endpoint to send a text message
@app.route('/send_message', methods=['POST'])
def send_message():
    user_phone = request.json['phone_number']
    message = client.messages.create(
        body='Reminder: Take your medication.',
        from_='your_phone_number',
        to=user_phone
    )
    return jsonify({'message': 'Message sent successfully.'})

if __name__ == '__main__':
    app.run(debug=True)
```


### Example Frontend Code (Bootstrap)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pain Management App</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css">
</head>
<body>
    <div class="container">
        <h1>Recovery Plan</h1>
        <form>
            <div class="mb-3">
                <label for="medication" class="form-label">Medication</label>
                <input type="text" class="form-control" id="medication" placeholder="Enter medication name">
            </div>
            <div class="mb-3">
                <label for="dosage" class="form-label">Dosage</label>
                <input type="text" class="form-control" id="dosage" placeholder="Enter dosage">
            </div>
            <button type="submit" class="btn btn-primary">Save</button>
        </form>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

---

This detailed prompt outlines the requirements for a pain management app that integrates user registration, injury tracking, recovery planning, and automated text messaging. It emphasizes the use of PostgreSQL for data storage, Twilio for text messaging, and Docker for deployment. The app should follow an MVC pattern and ensure secure data management and user authentication.

