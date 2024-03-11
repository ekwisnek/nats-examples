import cv2
import asyncio
import os
import schedule
import time
import json
import base64
import uuid
from datetime import datetime
from nats.aio.client import Client as NATS
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to check for the existence of a stream and create it if it doesn't exist
async def ensure_stream_exists():
    nats_url = os.getenv('NATS_URL')
    stream_name = os.getenv('NATS_STREAM_NAME')
    subject = os.getenv('NATS_SUBJECT')

    nc = NATS()
    await nc.connect(nats_url, user=os.getenv('NATS_USER'), password=os.getenv('NATS_PASSWORD'))
    js = nc.jetstream()

    try:
        # Try to get the stream info; if this fails, the stream does not exist
        await js.stream_info(stream_name)
        logging.info(f"Stream '{stream_name}' already exists.")
    except:
        # Stream does not exist, attempt to create it
        logging.info(f"Stream '{stream_name}' does not exist, attempting to create it...")
        await js.add_stream(name=stream_name, subjects=[f"{stream_name}.{subject}"])
        logging.info(f"Stream '{stream_name}' created successfully.")

    await nc.close()

# Capture image from webcam
def capture_image():
    cap = cv2.VideoCapture(0)  # 0 is the default webcam
    ret, frame = cap.read()
    if ret:
        # Save the frame as an image file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"captured_image_{timestamp}.jpg"
        cv2.imwrite(filename, frame)
        logging.info(f"Image captured and saved as {filename}")
    else:
        logging.error("Failed to capture image from webcam.")
    cap.release()
    cv2.destroyAllWindows()
    return filename if ret else None

# Send an image to NATS Jetstream with metadata
async def send_image_to_jetstream(image_path):
    nc = NATS()
    await nc.connect(
        os.getenv('NATS_URL'),
        user=os.getenv('NATS_USER'),
        password=os.getenv('NATS_PASSWORD')
    )

    js = nc.jetstream()

    with open(image_path, 'rb') as f:
        image_data = f.read()

    # Encode the image data using base64
    image_data_base64 = base64.b64encode(image_data).decode('utf-8')

    metadata = {
        "timestamp": datetime.now().isoformat(),
        "filename": image_path,
        "uuid": str(uuid.uuid4()),  # Generate a unique identifier for each image
    }
    message = {
        "metadata": metadata,
        "image_data": image_data_base64  # Base64 encoded string
    }

    await js.publish(
        f"{os.getenv('NATS_STREAM_NAME')}.{os.getenv('NATS_SUBJECT')}",
        json.dumps(message).encode('utf-8')
    )
    logging.info(f"Image '{image_path}' sent to NATS Jetstream with UUID {metadata['uuid']}.")

    await nc.drain()

# Scheduled job to capture and send an image
def job():
    image_path = capture_image()
    if image_path:
        asyncio.run(send_image_to_jetstream(image_path))

if __name__ == "__main__":
    asyncio.run(ensure_stream_exists())
    # Example: schedule to run every 10 seconds
    schedule.every(10).seconds.do(job)

    logging.info("Starting the image capture schedule...")
    while True:
        schedule.run_pending()
        time.sleep(1)
