import os

import boto3
import click

from process_msg import process_message
from botocore.config import Config

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
    queue = sqs.get_queue_by_name(QueueName=os.environ["QUEUE_NAME"])
    while True:
        messages = queue.receive_messages(MaxNumberOfMessages=10, WaitTimeSeconds=1,)
        for message in messages:
            try:
                process_message(message.body)
            except Exception as e:
                print(f"exception while processing message: {repr(e)}")
                continue

            message.delete()



if __name__ == "__main__":
    main()