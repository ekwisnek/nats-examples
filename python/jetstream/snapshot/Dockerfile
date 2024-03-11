# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory to /app
WORKDIR /app

# Install system dependencies (if you're not using Tesseract, you might not need this)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    ffmpeg libsm6 libxext6  # These are typical dependencies for opencv-python

# Copy the current directory contents into the container
COPY snapshot.py .

# Install any needed Python packages specified by your application
# This should include opencv-python and nats-py at least, based on your application's description
RUN pip install --no-cache-dir opencv-python nats-py schedule

# You can set environment variables that your application uses. For example:
ENV NATS_URL=nats://localhost:4222
ENV NATS_USER=user
ENV NATS_PASSWORD=password
ENV NATS_STREAM_NAME=default
ENV NATS_SUBJECT=default.subject

# The command to run when the container starts
CMD ["python", "./snapshot.py"]
