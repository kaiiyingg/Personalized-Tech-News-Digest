# Dockerfile optimized for Render free tier

# Use an official Python runtime as a parent image.
# Using Python 3.11-slim for a lightweight base image.
FROM python:3.11-slim

# Install system dependencies for psycopg2 (production version)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set the working directory inside the container.
WORKDIR /app

# Copy the requirements.txt file into the container.
COPY requirements.txt .

# Install Python packages with optimizations for free tier
# Use --no-cache-dir to reduce image size
# Install with minimal dependencies for transformers
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container.
COPY . .

# Set environment variables for production
ENV FLASK_APP=src/app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app
ENV TRANSFORMERS_CACHE=/tmp/transformers_cache
ENV HF_HOME=/tmp/huggingface_cache
ENV PYTORCH_TRANSFORMERS_CACHE=/tmp/transformers_cache
ENV TORCH_HOME=/tmp/torch_cache
# Memory optimization for AI models
ENV TOKENIZERS_PARALLELISM=false
ENV OMP_NUM_THREADS=1

# Expose the port your application will run on.
EXPOSE 8000

# Define the command to run when the container starts.
# Use single worker for free tier to save memory
CMD ["sh", "-c", "cd /app && gunicorn -w 1 -k sync -b 0.0.0.0:8000 --timeout 120 --graceful-timeout 60 --max-requests 1000 --max-requests-jitter 50 src.app:app"]
