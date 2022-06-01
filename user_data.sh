echo "Start setup" >> /tmp/setup.log
sudo yum update -y >> /tmp/setup.log
sudo yum install -y awslogs >> /tmp/setup.log
sudo systemctl start awslogsd >> /tmp/setup.log
sudo systemctl enable awslogsd.service >> /tmp/setup.log
echo "Installed aws logs" >> /tmp/setup.log

echo "[default]" >> ~/.aws/credentials
echo "aws_access_key_id = $AWS_ACCESS_KEY_ID" >> ~/.aws/credentials
echo "aws_secret_access_key = $AWS_SECRET_ACCESS_KEY" >> ~/.aws/credentials

aws ecr get-login-password \
    --region us-east-1 \
| docker login \
    --username AWS \
    --password-stdin 614871946825.dkr.ecr.us-east-1.amazonaws.com >> /tmp/setup.log

mkdir /tmp/outputs
docker run --gpus all -d --rm \
    --env AWS_REGION=us-east-1 \
    --env QUEUE_NAME=pollens-queue  \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$HOME/.aws/:/root/.aws/" \
    --mount type=bind,source=/tmp/outputs,target=/tmp/outputs \
    614871946825.dkr.ecr.us-east-1.amazonaws.com/pollinations/pollinator:76d5f1c31ff2257e8613fae02553b3dd16a651ee