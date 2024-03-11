# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install Tesseract OCR and other system dependencies
RUN apt-get update && \
    apt-get install -y tesseract-ocr libtesseract-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Make port available to the world outside this container
EXPOSE 4222

# Define environment variable
ENV NATS_URL=nats://your-nats-server:4222
ENV NATS_USER=yourUsername
ENV NATS_PASSWORD=yourPassword
ENV NATS_STREAM_NAME=image_stream
ENV NATS_SUBJECT=yourSubject

# Run ocr.py when the container launches
CMD ["python", "./ocr.py"]
