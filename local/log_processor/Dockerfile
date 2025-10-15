FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && \
    apt-get install -y default-libmysqlclient-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Create directory for downloaded logs
RUN mkdir -p /app/downloaded_logs

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .

# Make script executable
RUN chmod +x app.py

# Volume for downloaded logs
VOLUME ["/app/downloaded_logs"]

CMD ["python", "app.py"]
