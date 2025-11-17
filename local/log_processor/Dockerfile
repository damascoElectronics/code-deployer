FROM python:3.9-slim
WORKDIR /app

# Install MySQL client dependencies
RUN apt-get update && \
    apt-get install -y default-libmysqlclient-dev gcc && \
    rm -rf /var/lib/apt/lists/*

# Create directory for downloaded logs
RUN mkdir -p /app/downloaded_logs

# Copy requirements first (for Docker layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL Python files
COPY *.py ./
COPY processors/ ./processors/

# Verify files are copied (optional, for debugging)
RUN ls -la /app/

# Create directories
RUN mkdir -p /app/downloads/ogs /app/downloads/camera /app/downloads/weather


VOLUME ["/app/downloaded_logs"]

CMD ["python", "app.py"]
