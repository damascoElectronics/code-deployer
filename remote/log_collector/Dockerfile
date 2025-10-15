FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create logs directory
RUN mkdir -p /app/logs

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL Python files
COPY *.py ./

# Expose HTTP port
EXPOSE 8080

# Make script executable
RUN chmod +x app.py

# Volume for log files
VOLUME ["/app/logs"]

CMD ["python", "app.py"]