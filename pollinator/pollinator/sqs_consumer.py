import os
import json

import boto3
from botocore.config import Config
import botocore
import click

from process_msg import process_message


AWS_REGION =  os.environ.get('AWS_REGION', "us-east-1")
boto3_config = Config(
    region_name = AWS_REGION,
)


@click.command()
@click.option("--aws_endpoint", type=str, default=None, help="For localstack: http://localhost:4566 | For AWS: None")
@click.option("--aws_profile", type=str, default=None, help="For localstack: localstack | For AWS: aws_profile")
def main(aws_endpoint=None, aws_profile=None):
    sqs = boto3.client('sqs', config=boto3_config, region_name=AWS_REGION,
                         endpoint_url=aws_endpoint)
    queue_url = sqs.get_queue_url(
        QueueName=os.environ["QUEUE_NAME"]
    )['QueueUrl']
    while True:
        try:
            response = sqs.receive_message(
                QueueUrl=queue_url,
                AttributeNames=[
                    'SentTimestamp'
                ],
                MaxNumberOfMessages=1,
                MessageAttributeNames=[
                    'All'
                ],
                VisibilityTimeout=0,
                WaitTimeSeconds=1000
            )
        except botocore.exceptions.ReadTimeoutError:
            continue

        messages = response['Messages']

        for message in messages:
            # Delete received message from queue
            # try:
            process_message(json.loads(message['Body']))
            # except Exception as e:
            #     print(f"exception while processing message: {repr(e)}")

            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message['ReceiptHandle']
            )


if __name__ == "__main__":
    main()