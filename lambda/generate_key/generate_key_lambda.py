import os
import json
import random
import string
from http import HTTPStatus
import logging
from datetime import datetime
import boto3


# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Initialize the boto3 client for SQS
sqs_client = boto3.client("sqs")
queue_url = "https://sqs.us-east-1.amazonaws.com/381491929461/KeyIdQueue"


def get_random_id() -> str:
    """
    Function to generate a random string of 10 lowercase alphabets
    """
    return "".join(random.choices(string.ascii_lowercase, k=10))


def get_dynamodb_table(table_name: str) -> object:
    """
    Function to get the DynamoDB table object
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    return table


def save_to_dynamodb_table(table_name: str, transaction_id: str, request_params: dict):
    """
    Function to save a dictionary to DynamoDB table
    """
    table = get_dynamodb_table(table_name)

    # prediction_decimal = decimal.Decimal(str(prediction))
    datetime_sort_key = datetime.utcnow().isoformat()

    data_to_add = {
        "transaction_id": transaction_id,
        "creation_time": datetime_sort_key,
        "params": json.dumps(request_params),
        "status": "In progress",
    }

    table.put_item(Item=data_to_add)
    logger.info(f"Successful put to the table: {table_name}")
    logger.debug(f"Added data: {data_to_add}")


def handler(event, context):
    """
    Lambda function to generate key
    """
    logger.info("lambda_generate_key Handler started")

    try:
        # Parsing input data from the event object
        # Assuming event is directly the body of the request with necessary fields
        input_data = json.loads(event["body"])

        # Generating randon id to store the request in database
        random_id = get_random_id()
        logger.debug(f"Random id: {random_id}")

        # Saving to database
        table_name = os.environ["REQUESTS_TABLE_NAME"]
        save_to_dynamodb_table(
            table_name=table_name, transaction_id=random_id, request_params=input_data
        )

        message = {"transaction_id": random_id}

        # Sending the message to SQS
        sqs_response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message, indent=2),
        )

        if sqs_response is None:
            # Log the message ID of the message sent
            logger.info("Message ID:", sqs_response["MessageId"])

        # Constructing the success response
        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(message, indent=2),
            "headers": {"content-type": "application/json"},
        }

    except Exception as e:
        # Constructing the error response
        response = {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": json.dumps({"error": str(e)}),
            "headers": {"Content-Type": "application/json"},
        }

    return response
