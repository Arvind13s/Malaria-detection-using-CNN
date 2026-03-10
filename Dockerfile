FROM python:3.11-slim

WORKDIR /app

# Install system deps for TensorFlow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# HuggingFace Spaces expects port 7860
EXPOSE 7860

CMD ["python", "-c", "from app import create_app; create_app().run(host='0.0.0.0', port=7860)"]
