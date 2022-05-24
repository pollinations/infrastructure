# pollinator
- Read tasks from an SQS queue 
    [code taken from here](https://perandrestromhaug.com/posts/writing-an-sqs-consumer-in-python/)
- execute tasks
- stream outputs to topic specified in queue item

# Run locally
Install package:
```sh
# Install dependencies
pip install -e ".[test]"

# Install pre-commit hooks
brew install pre-commit
pre-commit install -t pre-commit
```

Install localstack
```
pip install localstack
```
Create an SQS queue (otherwise done by cdk)
```
export QUEUE_NAME=pollens-queue
echo 'LOCALSTACK_ENDPOINT_URL="http://localhost:4566"'
pip install awscli-local
localstack start &
aws configure --profile localstack
    AWS Access Key ID [None]: test
    AWS Secret Access Key [None]: test
    Default region name [None]: us-east-1
    Default output format [None]:
awslocal sqs create-queue --queue-name $QUEUE_NAME
```
And start the worker
```
python pollinator/sqs_consumer.py
```
Or build an run the image:
```
docker build -t pollinator .
docker run -p 8000:5000 --env-file .env pollinator
```
# Requests



