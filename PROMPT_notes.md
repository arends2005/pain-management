
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

1. Allow user to create an account

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
