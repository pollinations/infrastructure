# Infrastructure

# Deploy
## Manual
```
export DOCKER_DEFAULT_PLATFORM='linux/amd64'
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
Next, build the test cpu [cog image](cog-sample/README.md).

Then start the services for middleware or pollinator. It might require increasing the disk space and memory docker reserves for containers [more](https://stackoverflow.com/questions/41813774/no-space-left-on-device-when-pulling-an-image).

Sen messages:
```
curl -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.ealNyCRtZ0DDJWmexGomcWQll-57wsfMuL06J7MRVts" \
    -X POST \
    localhost:5555/pollen/ \
    -d '{"pollen_id": "my-pollen", "notebook": "test-image", "prompt": "A monkey enjoying a banana"}'
```


Send messages:
```
awslocal sqs send-message --queue-url http://localhost:4566/000000000000/pollens-queue --message-body "{1: 1}"
```