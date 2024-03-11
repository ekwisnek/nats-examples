import asyncio
import os
import json
import base64
from nats.aio.client import Client as NATS
import pytesseract
from PIL import Image
import io
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def consume_and_process_images():
    nats_url = os.getenv('NATS_URL')
    stream_name = os.getenv('NATS_STREAM_NAME')
    subject = os.getenv('NATS_SUBJECT')

    nc = NATS()
    await nc.connect(nats_url, user=os.getenv('NATS_USER'), password=os.getenv('NATS_PASSWORD'))
    js = nc.jetstream()

    async def message_handler(msg):
        data = json.loads(msg.data.decode('utf-8'))
        image_data_base64 = data['image_data']
        uuid = data['metadata']['uuid']

        # Decode the base64 image data
        image_data = base64.b64decode(image_data_base64)
        image = Image.open(io.BytesIO(image_data))

        try:
            # Perform OCR using pytesseract
            text = pytesseract.image_to_string(image)
            logging.info(f"Text recognized for image UUID {uuid}: {text[:30]}...")

            # Prepare the JSON output
            result = {
                "uuid": uuid,
                "text": text.strip() if text else "No text detected"
            }
            print(json.dumps(result, indent=2))
        except Exception as e:
            logging.error(f"Failed to process image UUID {uuid}: {str(e)}")

    # Subscribe to the stream and subject, setting the message handler
    await js.subscribe(f"{stream_name}.{subject}", cb=message_handler)

    logging.info("Subscribed to NATS stream and waiting for messages...")
    while True:
        # Keep the subscription active
        await asyncio.sleep(1)

if __name__ == "__main__":
    try:
        asyncio.run(consume_and_process_images())
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
