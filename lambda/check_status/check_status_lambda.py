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
    logger.info("check_status_lambda Handler started")

    try:
        # Getting the table name from env variables
        table_name = os.environ["REQUESTS_TABLE_NAME"]
        logger.debug(f"Table name: {table_name}")

        requests_table = get_dynamodb_table(table_name)

        key_id = event.get("pathParameters")["key_id"]
        logger.debug(f"key_id: {key_id}")

        # Extracting the request from the table
        response = requests_table.get_item(Key={"key_id": key_id})
        request_data = response.get("Item", {})
        json_request_data = json.dumps(request_data, cls=DecimalEncoder)
        logger.debug(f"json_request_data: {json_request_data}")

        # Getting the request_status from database
        request_status = request_data.get("status")
        result = {"request_status": request_status}

        # If status is done then add predictions as well
        if request_status == REQUEST_STATUS_DONE:
            result["prediction"] = request_data.get("prediction")

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(result, indent=2),
            "headers": {"content-type": "application/json"},
        }
    except Exception as e:
        response = {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": f"Exception={e}",
            "headers": {"content-type": "text/plain"},
        }
    return response
