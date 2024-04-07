## Fraud Detection Service

This project imitates real world production

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
