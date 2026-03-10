FROM python:3.11-slim

# Install system deps for TensorFlow / OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user (Hugging Face runs Docker containers as user 1000)
RUN useradd -m -u 1000 user
USER user

# Set home and path environment variables
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# Set the working directory inside the container
WORKDIR $HOME/app

# Copy requirements and install them securely as the 'user'
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project files with the correct ownership
COPY --chown=user:user . .

# Ensure the models directory exists so the app can save the .keras file
RUN mkdir -p models

# Expose the mandatory port for Hugging Face
EXPOSE 7860
ENV PORT=7860

# Launch the app
CMD ["python", "-c", "from app import create_app; create_app().run(host='0.0.0.0', port=7860)"]
