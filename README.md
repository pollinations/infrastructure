# Infrastructure

# Deploy
## Manual
```
cdk synth
cdk deploy
```

## CI
comming soon

# Repo summary
Infrastructure: see bees.drawio

Repo structure:
- middlepoll: middleware, deployed on ECS+Fargate, consumes from load balancer
    - authentication via jwt, validates with secret from secrets manager
    - accepts http requests via load balancer for pollens
    - puts pollens into an SQS queue
- pollinator: Worker, eployed on EC2+EC2 with GPU
    - reads from SQS queue
    - runs cog to generate outputs
    - runs ipfs syncing
- infrastructure: creates clusters, load balancer

# Development
Install localstack
```
pip install localstack awscli-local
```
Create an SQS queue (otherwise done by cdk)
```
aws configure --profile localstack
    AWS Access Key ID [None]: test
    AWS Secret Access Key [None]: test
    Default region name [None]: us-east-1
    Default output format [None]:

export QUEUE_NAME=pollens-queue
localstack start &
awslocal sqs create-queue --queue-name $QUEUE_NAME
```
Then start the services for middleware or pollinator.

Send messages:
```
awslocal sqs send-message --queue-url http://localhost:4566/000000000000/pollens-queue --message-body "{1: 1}"
```