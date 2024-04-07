from aws_cdk import (
    Stack,
    aws_lambda as lambda_,
    aws_apigatewayv2 as _apigw,
    Duration,
    aws_apigatewayv2_integrations as _integrations,
    CfnOutput,
    aws_dynamodb as dynamodb,
)

import os
from constructs import Construct
from os.path import dirname


DIRNAME = dirname(dirname(__file__))


class AntiFraudStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # POST lambda to generate key and store request in database
        lambda_generate_key = lambda_.Function(
            self,
            "AntifraudFunctionGenerate",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(os.path.join(DIRNAME, "lambda/generate_key")),
            handler="generate_key_lambda.lambda_generate_key",
            timeout=Duration.seconds(30),
            memory_size=256,
        )

        requests_table = dynamodb.TableV2(
            self,
            "RequestsTable",
            table_name="requests_table",
            partition_key=dynamodb.Attribute(
                name="key_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="request_start_time", type=dynamodb.AttributeType.STRING
            ),
        )

        requests_table.grant_read_write_data(lambda_generate_key)

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
            path="/gen_key",
            methods=[_apigw.HttpMethod.POST],
            integration=_integrations.HttpLambdaIntegration(
                "LambdaProxyIntegration", handler=lambda_generate_key
            ),
        )

        # Outputs
        CfnOutput(
            self,
            "API Endpoint",
            description="API Endpoint",
            value=http_api.api_endpoint,
        )
