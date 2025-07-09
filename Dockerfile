# Dockerfile

# Use an official Python runtime as a parent image.
# Using Python 3.11-slim-bullseye for a lightweight and up-to-date base image.
FROM python:3.11-slim-bullseye

# Set the working directory inside the container.
# All subsequent commands will run from this directory.
WORKDIR /app

# Copy the requirements.txt file into the container.
# This step is done separately so Docker can cache the 'pip install' layer.
# If only requirements.txt changes, this layer is rebuilt, not the whole app.
COPY requirements.txt .

# Install any needed Python packages specified in requirements.txt.
# '--no-cache-dir' reduces the image size by not storing pip's cache.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container.
# The '.' means copy everything from the current local directory (project root).
# The second '.' means copy to the current working directory inside the container (/app).
COPY . .

# Set environment variables for Flask.
# FLASK_APP tells Flask where your main application instance is.
# FLASK_RUN_HOST=0.0.0.0 makes the Flask development server accessible from outside the container.
ENV FLASK_APP=src/app.py
ENV FLASK_RUN_HOST=0.0.0.0
#Explicitly set port, though Flask's default is 5000
ENV FLASK_RUN_PORT=5000 

# Expose the port your Flask application will run on.
# This informs Docker that the container listens on this port.
EXPOSE 5000

# Define the command to run when the container starts.
# This will execute your database schema creation script first,
# then start the Flask development server.
# The '&&' ensures 'flask run' only executes if 'python src/database/connection.py' succeeds.
# Note: In a production setup, database migrations are usually run as a separate
# step (e.g., in a CI/CD pipeline or a dedicated init container) before the app starts.
# For this project, running it on container start is acceptable for simplicity.
CMD python src/database/connection.py && flask run