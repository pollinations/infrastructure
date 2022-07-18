import logging
import os

import dotenv
from realtime.connection import Socket
from supabase import Client, create_client

import json
import os
import time

import boto3
from botocore.config import Config
from retry import retry


dotenv.load_dotenv()
logging.basicConfig(format="%(asctime)s %(levelname)s:%(message)s", level=logging.INFO)


SUPABASE_ID: str = os.environ["SUPABASE_ID"]
API_KEY: str = os.environ["SUPABASE_API_KEY"]
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")

boto3_config = Config(region_name=AWS_REGION)
sqs = None
queue_url = None


@retry(tries=300, delay=1)
def wait_for_queue_url():
    print(f"Trying to get queue {os.environ['QUEUE_NAME']}")
    global sqs, queue_url
    sqs = boto3.client(
        "sqs", config=boto3_config, region_name=AWS_REGION
    )
    queue_url = sqs.get_queue_url(QueueName=os.environ["QUEUE_NAME"])["QueueUrl"]
    assert queue_url is not None
    print(f"Got queue url: {queue_url}")


def supabase_to_queue(payload):
    """Payload example:
    {
        'columns': [
            {'name': 'input', 'type': 'varchar'},
            {'name': 'output', 'type': 'varchar'},
            {'name': 'image', 'type': 'varchar'},
            {'name': 'start_time', 'type': 'timestamp'},
            {'name': 'end_time', 'type': 'timestamp'},
            {'name': 'logs', 'type': 'varchar'},
            {'name': 'request_submit_time', 'type': 'timestamp'}],
        'commit_timestamp': '2022-07-15T18:19:24Z',
        'errors': None,
        'record': {
            'end_time': None,
            'image': None,
            'input': 'iyg',
            'logs': None,
            'output': None,
            'request_submit_time': '2022-07-16T06:51:15',
            'start_time': None},
        'schema': 'public',
        'table': 'pollen',
        'type': 'INSERT'
    }
    """
    sqs.send_message(QueueUrl=queue_url, MessageBody=json.dumps(payload["record"]))


def main():
    """
    Run the server.
    """
    wait_for_queue_url()
    URL = f"wss://{SUPABASE_ID}.supabase.co/realtime/v1/websocket?apikey={API_KEY}&vsn=1.0.0"
    s = Socket(URL)
    s.connect()
    channel = s.set_channel("realtime:*")
    channel.join().on("INSERT", supabase_to_queue)
    s.listen()


if __name__ == "__main__":
    main()
