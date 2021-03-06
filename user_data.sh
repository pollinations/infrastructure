#!/bin/bash
echo "Start setup" >> /tmp/setup.log
sudo yum update -y >> /tmp/setup.log
sudo yum install -y awslogs >> /tmp/setup.log
sudo systemctl start awslogsd >> /tmp/setup.log
sudo systemctl enable awslogsd.service >> /tmp/setup.log
echo "Installed aws logs" >> /tmp/setup.log


mkdir /tmp/ipfs
chmod -R a+rw /tmp/

echo '
#!/bin/bash
aws ecr get-login-password \
    --region us-east-1 \
| docker login \
    --username AWS \
    --password-stdin 614871946825.dkr.ecr.us-east-1.amazonaws.com
docker pull 614871946825.dkr.ecr.us-east-1.amazonaws.com/pollinations/pollinator:latest \
    | grep "Status: Downloaded newer image" \
    && (docker kill pollinator && sleep 3 || echo Pollinator not running...)
docker run --gpus all -d --rm \
        --network host \
        --name pollinator \
        --env AWS_REGION=us-east-1 \
        --env QUEUE_NAME=$QUEUE_NAME  \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$HOME/.aws/:/root/.aws/" \
        --mount type=bind,source=/tmp/ipfs,target=/tmp/ipfs \
        614871946825.dkr.ecr.us-east-1.amazonaws.com/pollinations/pollinator:latest
' > /home/ec2-user/pull_updates_and_restart.sh


echo '
#!/bin/bash
aws ecr get-login-password \
    --region us-east-1 \
| docker login \
    --username AWS \
    --password-stdin 614871946825.dkr.ecr.us-east-1.amazonaws.com
curl -o images.json https://raw.githubusercontent.com/pollinations/model-index/main/images.json
curl -o fetch_images.py https://raw.githubusercontent.com/pollinations/model-index/main/fetch_images.py
python3 fetch_images.py | sh
' > /home/ec2-user/fetch_models.sh

crontab -l > fetch_updates
echo "*/5 * * * * sh /home/ec2-user/pull_updates_and_restart.sh &>> /tmp/pollinator.log" >> fetch_updates
echo "*/5 * * * * docker system prune -f &>> /tmp/prune.log" >> fetch_updates
echo "*/5 * * * * ps -ax | grep fetch_models | wc -l | grep 2 && sh /home/ec2-user/fetch_models.sh &>> /tmp/fetch.log" >> fetch_updates
crontab fetch_updates
rm fetch_updates


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
        --env QUEUE_NAME=$QUEUE_NAME  \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$HOME/.aws/:/root/.aws/" \
        --mount type=bind,source=/tmp/ipfs,target=/tmp/ipfs \
        614871946825.dkr.ecr.us-east-1.amazonaws.com/pollinations/pollinator:latest &>> /tmp/pollinator.log