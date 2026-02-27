# AI Hackathon Auto Apply Agent - Dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Set work directory
WORKDIR /app

# Install minimal system dependencies for PDF processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Cache bust v2 - Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && pip install beautifulsoup4

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads instance

# Expose port (Render uses 10000 by default)
EXPOSE 10000

# Run the application with Gunicorn
CMD gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 120 app:app
