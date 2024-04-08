import os
import json
import joblib
from http import HTTPStatus
import logging
import boto3
from decimal import Decimal
import pandas as pd
import time


# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

REQUEST_STATUS_DONE = "Done"
model = joblib.load("house_price_model.pkl")


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
        logger.info(f"event in calculate_prediction_lambda: {json.dumps(event)}")
        for record in event["Records"]:
            # Process each message
            transaction_dict = json.loads(record["body"])
            logger.info(f"transaction_dict: {json.dumps(transaction_dict)}")
            transaction_id_list.append(transaction_dict.get("transaction_id"))

        logger.info(f"transaction_id_list: {transaction_id_list}")

        # Getting the table name from env variables
        table_name = os.environ["REQUESTS_TABLE_NAME"]
        logger.info(f"Table name: {table_name}")

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

        logger.info(f"response after batch: {json.dumps(response)}")

        transactions_list = []
        status_list = []
        params_list = []
        creation_time_list = []

        data_to_add = {"rooms": [], "area": [], "floor": []}

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

            # data_to_add["transaction_id"].append(transaction_id)
            data_to_add["rooms"].append(params["rooms"])
            data_to_add["area"].append(params["area"])
            data_to_add["floor"].append(params["floor"])

            status_list.append(item.get("status").get("S"))

            logger.info(f"transaction_id: {transaction_id} ready")

        logger.info(f"data_to_add: {data_to_add}")
        logger.info(f"status_list: {json.dumps(status_list)}")

        logger.info(f"transactions_list: {json.dumps(transactions_list)}")

        inference_df = pd.DataFrame(data=data_to_add)

        # Inferencing the model
        start_time = time.time()
        predictions_list = model.predict(inference_df)
        end_time = time.time()
        inference_time = end_time - start_time
        logger.info(f"inference time: {inference_time}")
        logger.info(f"predictions_list: {predictions_list}")

        update_requests = []

        for (
            item_transaction_id,
            item_params,
            item_creation_time,
            item_prediction,
        ) in zip(transactions_list, params_list, creation_time_list, predictions_list):
            new_item = {
                "transaction_id": {"S": item_transaction_id},
                "status": {"S": REQUEST_STATUS_DONE},
                "prediction": {"N": str(item_prediction)},
                "params": {"S": item_params},
                "creation_time": {"S": item_creation_time},
            }
            update_requests.append({"PutRequest": {"Item": new_item}})

        # DynamoDB batch write request limit is 25 per batch
        # Assuming len(update_requests) <= 25 for simplicity
        update_response = dynamodb.batch_write_item(
            RequestItems={table_name: update_requests}
        )

        logger.info(f"update_response: {json.dumps(update_response)}")

        response = {
            "statusCode": HTTPStatus.OK.value,
            "body": json.dumps(update_response),
            "headers": {"content-type": "application/json"},
        }
    except Exception as e:
        logger.error(
            f"Exception={e}, event in calculate_prediction_lambda: {json.dumps(event)}"
        )
        response = {
            "statusCode": HTTPStatus.INTERNAL_SERVER_ERROR.value,
            "body": f"Exception={e}",
            "headers": {"content-type": "text/plain"},
        }
    return response
