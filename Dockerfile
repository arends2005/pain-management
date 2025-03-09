# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install netcat for the database connection check
RUN apt-get update && apt-get install -y netcat-openbsd && apt-get clean

# Copy the application code
COPY . .

# Create directories with proper permissions
RUN mkdir -p /app/app/static/uploads/profile_pics \
    && chmod -R 777 /app/app/static/uploads

# Make scripts executable
RUN chmod +x entrypoint.sh

# Expose the port the app runs on
EXPOSE 5000

# Use the entrypoint script to initialize the database and start the application
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command to run when starting the container
CMD ["python", "app.py"] 