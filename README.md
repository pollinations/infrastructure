# Infrastructure

# Deploy
## Manual
```
pip install -e .
export DOCKER_DEFAULT_PLATFORM='linux/amd64'
# if needed: export STAGE=prod
cdk synth
cdk deploy
```

# Request to the REST API:

## Example:
```
curl -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -X POST \
    Eleph-beecl-1OHF1H6OP0ANU-1012574990.us-east-1.elb.amazonaws.com/pollen/ \
    -d '{"notebook": "latent-diffusion", "ipfs": "QmRra7zGLpXYcnaPrgMtpqqpjtyXWQB63qxzjDXjU2fHrq"}'
```

Where the file structure in ipfs is:
```
/cid/
|--- inputs/
|            | ---Prompt: "avocado chair"
|            | ---init_image: "init.png"
|            | ---init.png
|            | ---...
|--- outputs/
```

This will be translated into the inputs for the cog model to
```
{
    "Prompt": "avocado chair",
    "init_image": "<ipfs-url>/inputs/init.png"
}
```

# Development with localstack (WIP)
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

    export QUEUE_NAME=pollens-queue-dev
    localstack start &
    awslocal sqs create-queue --queue-name $QUEUE_NAME
    ```
Next, build the test cpu [cog image](cog-sample/README.md).

Then start the services for middleware or pollinator. It might require increasing the disk space and memory docker reserves for containers [more](https://stackoverflow.com/questions/41813774/no-space-left-on-device-when-pulling-an-image).


Send messages:
```
awslocal sqs send-message --queue-url http://localhost:4566/000000000000/pollens-queue --message-body "{1: 1}"
```


