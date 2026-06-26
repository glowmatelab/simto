FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    nodejs \
    npm \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY . /app/
WORKDIR /app/

RUN pip install --no-cache-dir -r requirements.txt
RUN pip list

RUN mkdir -p downloads

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Render uses PORT env var — expose it
EXPOSE 8080

CMD ["python", "-m", "MusicBot"]
