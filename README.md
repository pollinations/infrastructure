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

Do one of:
- Start services all at once:
    ```
    export DOCKER_DEFAULT_PLATFORM=linux/amd64  
    docker-compose build
    docker-compose up
    ```
- test the cdk project locally
    ```
    npm install -g aws-cdk-local
    SERVICES=ecs,sqs,ec2 localstack start
    cdklocal deploy
    ```
- start services individually:
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

## Requests
Send messages:
```
# to localhost
curl -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.ealNyCRtZ0DDJWmexGomcWQll-57wsfMuL06J7MRVts" \
    -X POST \
    localhost:5555/pollen/ \
    -d '{"pollen_id": "my-pollen", "notebook": "test-image", "inputs": {"prompt": "A monkey enjoying a banana"}}'

# to load balancer
curl -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.IAsdG_P_c8SRPM4pniTaFypMq6v2zwTIDjqMgmlBh3o" \
    Infra-beecl-17H649Y0E2O8M-1159023412.us-east-1.elb.amazonaws.com/me/


curl -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.ealNyCRtZ0DDJWmexGomcWQll-57wsfMuL06J7MRVts" \
    -X POST \
    Infra-beecl-V9JONPAHSNUT-1257727326.us-east-1.elb.amazonaws.com/pollen/ \
    -d '{"pollen_id": "my-pollen", "notebook": "test-image", "prompt": "A monkey enjoying a banana"}'

curl -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.ealNyCRtZ0DDJWmexGomcWQll-57wsfMuL06J7MRVts" \
    -X POST \
    Backe-beecl-M843IRJ6T290-1562335207.us-east-1.elb.amazonaws.com/pollen/ \
    -d '{"pollen_id": "my-pollen", "notebook": "clip+vqgan", "inputs": {"drawer": "vqgan", "prompts": "yo"}}'
```


Send messages:
```
awslocal sqs send-message --queue-url http://localhost:4566/000000000000/pollens-queue --message-body "{1: 1}"
```


docker run -ti \
    -v  $HOME/.aws/:/root/.aws/ \
    -e AWS_REGION=us-east-1 \
    -e QUEUE_NAME=pollens_queue \
    --net infrastructure_default \
    infrastructure_pollinator \
    /bin/bash