#!/bin/bash
echo "Start setup" >> /tmp/setup.log
sudo yum update -y >> /tmp/setup.log
sudo yum install -y awslogs >> /tmp/setup.log
sudo systemctl start awslogsd >> /tmp/setup.log
sudo systemctl enable awslogsd.service >> /tmp/setup.log
echo "Installed aws logs" >> /tmp/setup.log


mkdir /tmp/ipfs

echo '
#!/bin/bash
aws ecr get-login-password \
    --region us-east-1 \
| docker login \
    --username AWS \
    --password-stdin 614871946825.dkr.ecr.us-east-1.amazonaws.com
docker pull 614871946825.dkr.ecr.us-east-1.amazonaws.com/pollinations/pollinator:latest \
    | grep "Status: Downloaded newer image" \
    && (docker kill pollinator || echo Pollinator not running...) \
    && docker run --gpus all -d --rm \
        --network host \
        --name pollinator \
        --env AWS_REGION=us-east-1 \
        --env QUEUE_NAME=pollens-queue  \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$HOME/.aws/:/root/.aws/" \
        --mount type=bind,source=/tmp/ipfs,target=/tmp/ipfs \
        614871946825.dkr.ecr.us-east-1.amazonaws.com/pollinations/pollinator:latest
' > ~/pull_updates_and_restart.sh

# Pull for updates every full hour
crontab -l > restart_cron
echo "*/5 * * * * sh ~/pull_updates_and_restart.sh &>> /tmp/pollinator.log" >> restart_cron
crontab restart_cron
rm restart_cron

aws ecr get-login-password \
    --region us-east-1 \
| docker login \
    --username AWS \
    --password-stdin 614871946825.dkr.ecr.us-east-1.amazonaws.com
docker pull 614871946825.dkr.ecr.us-east-1.amazonaws.com/pollinations/pollinator:latest

docker run --gpus all -d --rm \
        --network host \
        --name pollinator \
        --env AWS_REGION=us-east-1 \
        --env QUEUE_NAME=pollens-queue  \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$HOME/.aws/:/root/.aws/" \
        --mount type=bind,source=/tmp/ipfs,target=/tmp/ipfs \
        614871946825.dkr.ecr.us-east-1.amazonaws.com/pollinations/pollinator:latest &>> /tmp/pollinator.log