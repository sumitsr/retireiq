FROM python:3.11-slim

WORKDIR /app

# Ensure we have required system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Download Spacy model separately so it doesn't redownload on code changes
RUN python -m spacy download en_core_web_sm

COPY . .

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 5000

# Dev server with hot-reload
CMD ["python", "run.py"]
