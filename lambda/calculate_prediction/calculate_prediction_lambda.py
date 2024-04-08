import os
import json
from http import HTTPStatus
import logging
import boto3
from decimal import Decimal


# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

REQUEST_STATUS_DONE = "Done"


class DecimalEncoder(json.JSONEncoder):
    """
    Encoder for int values that are stored in DynamoDB as Decimal
    """

    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super(DecimalEncoder, self).default(o)


def get_dynamodb_table(table_name: str) -> object:
    """
    Function to get the DynamoDB table object
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)
    return table


def handler(event, context) -> dict:
    """
    Lambda function to get status from dynamodb and if done get predictions
    """
    logger.info("calculate_prediction_lambda Handler started")

    transaction_id_list = []

    try:
        logger.info(
            f"event in calculate_prediction_lambda: {json.dumps(event, indent=2)}"
        )
        for record in event["Records"]:
            # Process each message
            result = json.loads(record["body"])
            logger.info(f"result: {json.dumps(result, indent=2)}")
            transaction_id_list.append(result.get("transaction_id"))

        logger.info(f"transaction_id_list: {transaction_id_list}")

        # Getting the table name from env variables
        table_name = os.environ["REQUESTS_TABLE_NAME"]
        logger.info(f"Table name: {table_name}")

        request = {
            "transactions_table": {
                "Keys": [
                    {"transaction_id": {"S": value}} for value in transaction_id_list
                ],
            }
        }

        dynamodb = boto3.client("dynamodb")

        # Fetch the items
        response = dynamodb.batch_get_item(RequestItems=request)

        logger.info(f"response after batch: {json.dumps(response, indent=2)}")

        # Access the returned items
        items = response["Responses"][table_name]
        for item in items:
            logger.info(f"Item: {item}")

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(result, indent=2),
            "headers": {"content-type": "application/json"},
        }
    except Exception as e:
        logger.error(
            f"Exception={e}, event in calculate_prediction_lambda: {json.dumps(event, indent=2)}"
        )
        response = {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": f"Exception={e}",
            "headers": {"content-type": "text/plain"},
        }
    return response
