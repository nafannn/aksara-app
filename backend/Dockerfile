# Bangun dari ROOT repo:  docker build -f backend/Dockerfile -t aksara-backend .
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    TF_ENABLE_ONEDNN_OPTS=0 \
    AKSARA_AUDIO_DIR=/data/aksara-audio \
    PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt backend/requirements.txt
COPY vision/requirements.txt vision/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt -r vision/requirements.txt gunicorn

COPY backend backend
COPY vision vision

# Satu worker: model TensorFlow dimuat sekali dan dibagi antar thread.
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 120 backend.app:app"]
