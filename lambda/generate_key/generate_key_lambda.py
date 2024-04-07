import json
import random
import string
from http import HTTPStatus
import logging


# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_random_id() -> str:
    """
    Function to generate a random string of 10 lowercase alphabets
    """
    return "".join(random.choices(string.ascii_lowercase, k=10))


def lambda_generate_key(event, context):
    """
    Lambda function to generate key
    """
    logger.info("lambda_generate_key Handler started")

    try:

        random_id = get_random_id()

        logger.info(f"{random_id=}")

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps({"key_id": random_id}, indent=2),
            "headers": {"content-type": "application/json"},
        }
    except Exception as e:
        response = {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": f"Exception={e}",
            "headers": {"content-type": "text/plain"},
        }
    return response
