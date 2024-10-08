# import the flask web framework

import json
import redis as redis
from flask import Flask, request
from loguru import logger
from flask import Flask
HISTORY_LENGTH = 10
DATA_KEY = "engine_temperature"
# create a Flask server, and allow us to interact with it using the app variable
app = Flask(__name__)


# define an endpoint which accepts POST requests, and is reachable from the /record endpoint
@app.route('/record', methods=['POST'])
def record_engine_temperature():
    payload = request.get_json(force=True)
    logger.info(f"(*) record request --- {json.dumps(payload)} (*)")

    engine_temperature = payload.get("engine_temperature")
    logger.info(f"engine temperature to record is: {engine_temperature}")

    database = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)
    database.lpush(DATA_KEY, engine_temperature)
    logger.info(f"stashed engine temperature in redis: {engine_temperature}")

    while database.llen(DATA_KEY) > HISTORY_LENGTH:
        database.rpop(DATA_KEY)
    engine_temperature_values = database.lrange(DATA_KEY, 0, -1)
    logger.info(f"engine temperature list now contains these values: {engine_temperature_values}")

    logger.info(f"record request successful")
    return {"success": True}, 200


# practically identical to the above
@app.route('/collect', methods=['GET'])
def collect_engine_temperature():
    database = redis.Redis(host="redis", port=6379, db=0, decode_responses=True)

    # Fetch all stored temperatures
    engine_temperature_values = database.lrange(DATA_KEY, 0, -1)

    if engine_temperature_values:
        # Convert all values to floats to calculate the average
        engine_temperature_values = [float(temp) for temp in engine_temperature_values]
        current_temperature = engine_temperature_values[0]  # Most recent temperature
        average_temperature = sum(engine_temperature_values) / len(engine_temperature_values)
    else:
        # Handle case when no temperatures are stored
        current_temperature = None
        average_temperature = None

    logger.info(f"Current engine temperature: {current_temperature}")
    logger.info(f"Average engine temperature: {average_temperature}")

    return {
        "current_engine_temperature": current_temperature,
        "average_engine_temperature": average_temperature
    }, 200

