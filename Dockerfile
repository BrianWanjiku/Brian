FROM python:3.11-slim

# Install system dependencies for OpenCV, dlib (face_recognition), and PyAudio
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libx11-dev \
    libatlas-base-dev \
    libgtk-3-dev \
    libboost-python-dev \
    libopencv-dev \
    portaudio19-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy loop source code
COPY . /app

# The primary Sovereign orchestrator
CMD ["python", "main.py"]
