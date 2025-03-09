# Pain Management App

A comprehensive web application for tracking injury recovery, managing treatment plans, and receiving automated text message reminders.

## Features

- **User Registration and Authentication**: Secure account creation with invite code requirement
- **Injury Tracking**: Record and monitor injuries with severity, type, and location
- **Recovery Plans**: Create customized recovery plans with medications and exercises
- **Progress Monitoring**: Track pain levels and mobility over time with visual charts
- **Text Message Reminders**: Receive SMS reminders for medications and exercises
- **Admin Dashboard**: Manage users, injuries, and recovery plans

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL
- **Frontend**: Bootstrap, Plotly.js
- **SMS Integration**: Twilio API
- **Deployment**: Docker, Docker Compose

## Setup and Installation

### Prerequisites

- Docker and Docker Compose
- Twilio account (for SMS functionality)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pain-management.git
   cd pain-management
   ```

2. Create a `.env` file based on the provided `.env.sample`:
   ```
   cp .env.sample .env
   ```

3. Update the `.env` file with your specific configuration:
   - Set your Twilio credentials
   - Configure database settings
   - Set a secure session secret
   - Customize the invite code

4. Build and start the Docker containers:
   ```
   docker-compose up -d
   ```

5. Access the application at `http://localhost:5000`

## Usage

### User Workflow

1. Register with the provided invite code
2. Add injuries and create recovery plans
3. Log progress and track recovery
4. Receive and respond to text message reminders

### Admin Workflow

1. Log in with admin credentials
2. Manage users, injuries, and recovery plans
3. View analytics and progress data

## Development

### Project Structure

```
pain-management/
├── app/
│   ├── controllers/      # Route handlers
│   ├── models/           # Database models
│   ├── forms/            # Form definitions
│   ├── templates/        # HTML templates
│   └── static/           # CSS, JS, images
├── config/               # Configuration files
├── migrations/           # Database migrations
├── .env                  # Environment variables
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
└── requirements.txt      # Python dependencies
```

### Database Management

The application uses SQLAlchemy to manage the database schema:

1. **Automatic Schema Creation**: When the container starts, the application automatically creates all necessary database tables.

2. **Schema Updates**: When the database schema changes (e.g., new fields are added to models):
   - The changes are automatically applied when the container restarts
   - No manual migration steps are required

3. **Database Reset**: If you need to reset the database:
   ```
   docker-compose down -v  # This removes the database volume
   docker-compose up -d    # Start again with a fresh database
   ```

### Running Tests

```
docker-compose exec web python -m pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- Flask and its extensions
- Bootstrap for the UI components
- Twilio for SMS functionality
- Plotly.js for data visualization

## Security Best Practices

### Environment Variables
This application uses environment variables for all sensitive configuration. Before deploying:

1. **Never commit `.env` files to version control**
   - The `.env` file contains sensitive credentials and should be excluded in `.gitignore`
   - Use `.env.sample` as a template to create your own `.env` file

2. **Use strong, unique passwords**
   - Generate a secure random string for `SESSION_SECRET`:
     ```
     python -c "import secrets; print(secrets.token_hex(64))"
     ```
   - Use strong passwords for database and admin accounts

3. **Credentials rotation**
   - Regularly rotate your Twilio API credentials and database passwords
   - Update the `.env` file when credentials change

### Development vs Production
- Default values provided in `config.py` are **for development only**
- In production, **always** set all environment variables explicitly
- Set `FLASK_ENV=production` in production to disable development defaults

### Docker Security
- Review Docker container permissions
- The uploads directory uses 777 permissions for simplicity, but consider more restrictive permissions in production
