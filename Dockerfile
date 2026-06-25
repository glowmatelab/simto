FROM python:3.11-slim

# ffmpeg needed for PyTgCalls audio streaming
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# downloads/ folder for audio files (ephemeral on Render)
RUN mkdir -p downloads

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

CMD ["python", "-m", "MusicBot"]
