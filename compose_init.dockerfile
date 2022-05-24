FROM python:3.9

RUN apt-get update && apt-get install -y curl
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install

CMD aws --endpoint-url=http://localstack:4566 sqs create-queue --queue-name $QUEUE_NAME
