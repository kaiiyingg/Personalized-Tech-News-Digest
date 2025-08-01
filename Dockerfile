# Dockerfile

# Use an official Python runtime as a parent image.
# Using Python 3.11-slim-bullseye for a lightweight and up-to-date base image.
FROM python:3.11-slim-bullseye

# Install system dependencies for psycopg2 (production version)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

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


# Set environment variables for production
ENV FLASK_APP=src/app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose the port your application will run on.
EXPOSE 8000

# Define the command to run when the container starts.
# Use gunicorn for production instead of Flask dev server
CMD ["sh", "-c", "cd /app && gunicorn -w 2 -k gevent -b 0.0.0.0:8000 --timeout 600 --graceful-timeout 300 --preload src.app:app"]
