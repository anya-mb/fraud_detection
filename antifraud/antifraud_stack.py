from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_apigatewayv2 as _apigw,
    Duration,
    aws_apigatewayv2_integrations as _integrations,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_sqs as sqs,
    aws_lambda_event_sources as event_sources,
)

import os
from constructs import Construct
from os.path import dirname


DIRNAME = dirname(dirname(__file__))


class AntiFraudStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # dynamodb table to store all the requests info
        requests_table = dynamodb.TableV2(
            self,
            "RequestsTable",
            table_name="transactions_table",
            partition_key=dynamodb.Attribute(
                name="transaction_id", type=dynamodb.AttributeType.STRING
            ),
        )

        # POST lambda to generate key and store request in database
        lambda_generate_key = lambda_.Function(
            self,
            "AntifraudFunctionGenerate",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(os.path.join(DIRNAME, "lambda/generate_key")),
            handler="generate_key_lambda.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "REQUESTS_TABLE_NAME": requests_table.table_name,
            },
        )

        # GET lambda to check the status of request in database and send status or result back
        lambda_check_status = lambda_.Function(
            self,
            "AntifraudFunctionCheckStatus",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(os.path.join(DIRNAME, "lambda/check_status")),
            handler="check_status_lambda.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "REQUESTS_TABLE_NAME": requests_table.table_name,
            },
        )

        lambda_calculate_prediction = lambda_.Function(
            self,
            "AntifraudFunctionCalculatePrediction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(
                os.path.join(DIRNAME, "lambda/calculate_prediction")
            ),
            handler="calculate_prediction_lambda.handler",
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "REQUESTS_TABLE_NAME": requests_table.table_name,
            },
        )

        # Granting lambdas permissions for the database
        requests_table.grant_read_write_data(lambda_generate_key)
        requests_table.grant_read_data(lambda_check_status)
        requests_table.grant_read_write_data(lambda_calculate_prediction)

        queue = sqs.Queue(
            self,
            "MyQueue",
            queue_name="KeyIdQueue",
            visibility_timeout=Duration.seconds(300),
            receive_message_wait_time=Duration.seconds(10),
        )

        # Grant the Lambda function permissions to write to the SQS queue
        queue.grant_send_messages(lambda_generate_key)

        lambda_calculate_prediction.add_event_source(
            event_sources.SqsEventSource(
                queue,
                max_batching_window=Duration.seconds(60),
                batch_size=3,  # Number of messages to process per Lambda invocation
            )
        )

        # Configure API Gateway
        http_api = _apigw.HttpApi(
            self,
            "MyHttpApi",
            cors_preflight=_apigw.CorsPreflightOptions(
                allow_methods=[_apigw.CorsHttpMethod.GET],
                allow_origins=["*"],
                max_age=Duration.days(10),
            ),
        )

        http_api.add_routes(
            path="/transaction",
            methods=[_apigw.HttpMethod.POST],
            integration=_integrations.HttpLambdaIntegration(
                "LambdaProxyIntegration", handler=lambda_generate_key
            ),
        )

        http_api.add_routes(
            path="/transaction/{key_id}",
            methods=[_apigw.HttpMethod.GET],
            integration=_integrations.HttpLambdaIntegration(
                "LambdaProxyIntegration", handler=lambda_check_status
            ),
        )

        # Outputs
        CfnOutput(
            self,
            "API Endpoint",
            description="API Endpoint",
            value=http_api.api_endpoint,
        )
