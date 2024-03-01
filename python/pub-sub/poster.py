from flask import Flask, request, jsonify
from jsonschema import validate, ValidationError
import asyncio
import json
import logging
import nats
from nats.errors import TimeoutError, ConnectionClosedError, NoServersError
import argparse

# Setup argparse for command-line arguments
parser = argparse.ArgumentParser(description='Run a Flask application with configurable NATS integration.')
parser.add_argument('--port', type=int, default=5000, help='Port on which to listen')
parser.add_argument('--nats-server', type=str, default='nats://localhost:4222', help='NATS server address')
parser.add_argument('--nats-subject', type=str, default='hello.world', help='NATS subject to publish to')
args = parser.parse_args()

app = Flask(__name__)

# JSON Schema for validation
schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "age": {"type": "integer"},
        "email": {"type": "string", "format": "email"}
    },
    "required": ["name", "age", "email"]
}

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/v1/api', methods=['POST'])
async def handle_request():
    nc = await nats.connect(args.nats_server)  # Connect to NATS server
    try:
        data = request.get_json()
        validate(instance=data, schema=schema)  # Validate JSON against schema
        await nc.publish(args.nats_subject, json.dumps(data).encode('utf-8'))  # Publish message to "hello.world" subject
        logger.debug("Published message to %s: %s", args.nats_subject, data)
        return jsonify({"message": "Data received and published successfully"}), 200
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400  # Bad request if JSON schema validation fails
    except NoServersError as e:
        logger.error("No NATS servers available for connection: %s", str(e))
        return jsonify({"error": "Service unavailable, please try again later."}), 503  # Service Unavailable
    except ConnectionClosedError as e:
        logger.error("Connection to NATS was closed unexpectedly: %s", str(e))
        return jsonify({"error": "Connection lost, please try again."}), 503  # Service Unavailable
    except TimeoutError as e:
        logger.error("Error publishing message: %s", str(e))
        return jsonify({"error": str(e)}), 500  # Internal server error if NATS issues occur

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    app.run(debug=True, port=args.port)
