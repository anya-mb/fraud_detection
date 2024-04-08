FROM amazon/aws-lambda-python:latest
# FROM public.ecr.aws/lambda/python:3.11


# Install dependencies
RUN pip install scikit-learn joblib boto3 pandas

# Copy files
COPY calculate_prediction_lambda.py ${LAMBDA_TASK_ROOT}
COPY house_price_model.pkl ${LAMBDA_TASK_ROOT}

# Command to run the app
CMD [ "calculate_prediction_lambda.handler" ]
