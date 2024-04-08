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
            transaction_dict = json.loads(record["body"])
            logger.info(f"transaction_dict: {json.dumps(transaction_dict, indent=2)}")
            transaction_id_list.append(transaction_dict.get("transaction_id"))

        logger.info(f"transaction_id_list: {transaction_id_list}")

        # Getting the table name from env variables
        table_name = os.environ["REQUESTS_TABLE_NAME"]
        logger.info(f"Table name: {table_name}")

        # request = {
        #     "transactions_table": {
        #         "Keys": [
        #             {"transaction_id": {"S": value}} for value in transaction_id_list
        #         ],
        #     }
        # }

        request = {
            table_name: {
                "Keys": [
                    {"transaction_id": {"S": value}} for value in transaction_id_list
                ],
            }
        }

        dynamodb = boto3.client("dynamodb")

        # Fetch the items
        response = dynamodb.batch_get_item(RequestItems=request)

        logger.info(f"response after batch: {json.dumps(response, indent=2)}")

        transactions_list = []
        status_list = []
        params_list = []
        creation_time_list = []

        data_to_add = {"transaction_id": [], "rooms": [], "area": [], "floor": []}

        # Access the returned items
        items = response["Responses"][table_name]
        for item in items:
            logger.info(f"Item: {item}")

            transaction_id = item.get("transaction_id").get("S")
            transactions_list.append(transaction_id)

            creation_time = item.get("creation_time").get("S")
            creation_time_list.append(creation_time)

            params = item.get("params").get("S")
            params_list.append(params)
            logger.info("params: ")
            logger.info(f"params: {params}")

            params = json.loads(params)

            data_to_add["transaction_id"].append(transaction_id)
            data_to_add["rooms"].append(params["rooms"])
            data_to_add["area"].append(params["area"])
            data_to_add["floor"].append(params["floor"])

            status_list.append(item.get("status").get("S"))

            logger.info(f"transaction_id: {transaction_id} ready")

        logger.info(f"data_to_add: {json.dumps(data_to_add, indent=2)}")
        logger.info(f"status_list: {json.dumps(status_list, indent=2)}")

        logger.info(f"transactions_list: {json.dumps(transactions_list, indent=2)}")

        update_requests = []
        prediction_value = 10

        for item_transaction_id, item_params, item_creation_time in zip(
            transactions_list, params_list, creation_time_list
        ):
            new_item = {
                "transaction_id": {"S": item_transaction_id},
                "status": {"S": REQUEST_STATUS_DONE},
                "prediction": {"N": str(prediction_value)},
                "params": {"S": item_params},
                "creation_time": {"S": item_creation_time},
            }
            update_requests.append({"PutRequest": {"Item": new_item}})

        # DynamoDB batch write request limit is 25 per batch
        # Assuming len(update_requests) <= 25 for simplicity
        # update_response = dynamodb.batch_write_item(RequestItems={'transactions_table': update_requests})
        update_response = dynamodb.batch_write_item(
            RequestItems={table_name: update_requests}
        )

        logger.info(f"update_response: {json.dumps(update_response, indent=2)}")

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(update_response, indent=2),
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
