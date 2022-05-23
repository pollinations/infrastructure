import boto3
import os
import json

sqs = boto3.client('sqs')

queue_name = os.environ['QUEUE_NAME']

queue_url = sqs.get_queue_url(QueueName=queue_name)['QueueUrl']

def delete_sqs_message(receipt_handle):
    print(f"Deleting message {receipt_handle}")
    # Delete received message from queue
    sqs.delete_message(
        QueueUrl=queue_url,
        ReceiptHandle=receipt_handle
    )


# Read SQS
def read_sqs():
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
        WaitTimeSeconds=0
    )
    if 'Messages' in response:
        for message in response['Messages']:
            receipt_handle = message['ReceiptHandle']
            print(f"Received message {json.dumps(message})")
            delete_sqs_message(receipt_handle)
            return message
    else:
        return None


while True:
    message = read_sqs()
    # Take custom actions based on the message contents
    print(f"Activating {message}")
    print(f"Said Hello")
    if message:
        # Delete Message 
        delete_sqs_message(message['ReceiptHandle'])
        print(f"Finished for {message}")