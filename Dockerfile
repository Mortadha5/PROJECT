FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create uploads directory
RUN mkdir -p /app/static/uploads/avatars

# Expose port
EXPOSE 5555

# Run with gunicorn in production
CMD ["gunicorn", "--bind", "0.0.0.0:5555", "--workers", "3", "--timeout", "120", "app:app"]
