FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./


RUN mkdir -p /app/collected_data

EXPOSE 8080

CMD ["python", "app.py"]
