## Fraud Detection Service

A scalable, serverless fraud detection system leveraging multiple AWS services, including Lambda functions for serverless computation, DynamoDB for storage, SQS for message queuing and various other components for model storage and monitoring. This architecture ensures efficient processing, scalability and robustness in handling fraud detection tasks.

## Diagram
![fraud_detection_diagram](https://github.com/user-attachments/assets/44ff5c6e-3808-4773-9661-98a1408a47e3)



The diagram represents a serverless architecture for a fraud detection system using AWS services. Below is a detailed description of the components and their interactions:

1. User Request:

* A user sends a request via the API Gateway.

2. Load Balancer (LB):

* The request is forwarded to the Load Balancer, which distributes the incoming traffic.

3. AWS Lambda (Key Generation):

* An AWS Lambda function generates a unique key_id for the request and returns it to the user.
* This Lambda function also stores the request parameters in AWS DynamoDB, including the key_id, creation_time, params, and status.

4. AWS DynamoDB:

* Stores request details and serves as the database for tracking request statuses and predictions.
* Adds the key_id to an SQS queue for processing.

5. AWS SQS (Queue):

* Queues the request for batch processing.
* When there is a batch of transactions of size N or when a specified time T has passed, the batch is pushed to AWS Lambda for processing.
* If an SQS message fails to be processed after three retries, it is added to a Dead Letter Queue (DLQ), which triggers an alarm.

6. AWS Lambda (Prediction Calculation):

* Processes the queued batch of transactions.
* Retrieves the model from Model Blob Storage and features from Features DB.
* Calculates predictions and checks if the user is on any sanctions list from the Watchlist DB.
* Once processing is complete, the status is updated to "Done" and the prediction results are stored back in DynamoDB.

7. AWS Lambda (Status Check):

* Another Lambda function can be invoked to check the status of the prediction using the key_id.
* If the status is "Done", it returns the prediction results.

8. Drift Monitoring:

* A scheduled job triggers a Lambda function to monitor data drift.
* If drift is detected, the model is retrained to ensure accuracy.


## Setup

To install dependencies:

```
poetry install
```

Install pre-commit hooks:
```
poetry run pre-commit install
```


Add new python dependency:
```
poetry add new-package-name
```


### Deployment

Activate environment (optional):
```
poetry shell
```

Export environment variables for AWS CDK:

```
export AWS_ACCESS_KEY_ID=
export AWS_SECRET_ACCESS_KEY=
```

Deploy:

```
cdk deploy
```
