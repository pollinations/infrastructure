import os
from typing import Union
import json

import click
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
import boto3
from botocore.config import Config

load_dotenv()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

SECRET_KEY = os.getenv("secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


AWS_REGION =  os.environ.get('AWS_REGION', "us-east-1")
boto3_config = Config(
    region_name = AWS_REGION,
)

sqs = None
queue_url = None


def send_message(node_id, pollen):
    while True:
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


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class Pollen(BaseModel):
    pollen_id: str
    notebook: str


def get_sample_token(username):
    # TODO remove this to test
    token = jwt.encode({"sub": username}, SECRET_KEY, algorithm=ALGORITHM)
    return token


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data


@app.get("/")
def read_root():
    return {"health": "ok"}


@app.get("/me/", response_model=TokenData)
async def read_users_me(current_user: TokenData = Depends(get_current_user)):
    return current_user


@app.post("/pollen/", response_model=Pollen)
def send_message(pollen: Pollen):
    print(f"received message: {pollen}")
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(pollen.dict())
    )
    return pollen


@click.command()
@click.option("--port", type=int, default=5555)
@click.option("--host", default="0.0.0.0")
@click.option("--aws_endpoint", type=str, default=None, help="For localstack: http://localhost:4566 | For AWS: None")
@click.option("--aws_profile", type=str, default=None, help="For localstack: localstack | For AWS: aws_profile")
def main(port: int, host: str, aws_endpoint=None, aws_profile=None):
    """
    Run the server.
    """
    global sqs, queue_url
    sqs = boto3.client('sqs', config=boto3_config, region_name=AWS_REGION,
                         endpoint_url=aws_endpoint)
    queue_url = sqs.get_queue_url(
        QueueName=os.environ["QUEUE_NAME"]
    )['QueueUrl']

    import uvicorn

    print("sample token", get_sample_token("test"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
