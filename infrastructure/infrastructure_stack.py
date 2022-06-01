from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_s3 as s3,
    aws_s3_notifications as s3_notifications,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_sns_subscriptions as sns_subscriptions,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_logs as logs,
    aws_cloudwatch as cw,
    aws_cloudwatch_actions as cw_actions,
    aws_ecr as ecr,
    aws_secretsmanager as sm,
    aws_autoscaling as autoscaling,
)
from aws_cdk.aws_ecr_assets import DockerImageAsset
from constructs import Construct
import os


# with open("./pollinator/user_data.sh") as f:
#     user_data = f.read()
user_data = ("docker run --gpus all --env AWS_REGION=us-east-1 --env QUEUE_NAME=pollens-queue "
    '-v "/var/run/docker.sock:/var/run/docker.sock"'
    "614871946825.dkr.ecr.us-east-1.amazonaws.com/pollinations/pollinator:76d5f1c31ff2257e8613fae02553b3dd16a651ee")
class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC and Subnets for the ECS Cluster
        vpc = ec2.Vpc(self, "VPC",
                        max_azs=3,
                    )

        # Create EC2 machines for pollinator
        role = iam.Role(self, "InstanceSSM", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        role.add_to_policy(iam.PolicyStatement(actions=["sqs:*"], resources=["*"]))
        # Add read access to ECR
        role.add_to_policy(iam.PolicyStatement(actions=["ecr:*"], resources=["*"]))
        
        pollinator_ec2 = ec2.Instance(self, "PollinatorEC2",
            instance_type=ec2.InstanceType("g4dn.xlarge"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(hardware_type=ecs.AmiHardwareType.GPU), 
            key_name="pollinations-aws-key",
            role=role,
            vpc=vpc,
            user_data=ec2.UserData.custom(user_data))

        # Create SQS queue
        queue_name = "pollens-queue"
        sqs_queue = sqs.Queue(self, "SQSQueue", queue_name=queue_name)

        # Create middleware ecs cluster
        image = ecs.ContainerImage.from_asset(directory=os.path.join(".", "middlepoll"), build_args={"platform": "linux/amd64"})
        
        role = iam.Role(self, "FargateContainerRole", assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"))
        role.add_to_policy(iam.PolicyStatement(actions=["sqs:*"], resources=["*"]))

        # Create ECS pattern for the ECS Cluster
        cluster = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "bee-cluster",
            vpc=vpc,
            # security_group=ec2.SecurityGroup(self, "SecurityGroup", vpc=vpc),
            public_load_balancer=True,
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=image,
                container_port=5000,
                environment={
                    "DEBUG": "True",
                    "LOG_LEVEL": "DEBUG",
                    "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "QUEUE_NAME": queue_name,
                },
                secrets={
                    "secret_key": ecs.Secret.from_secrets_manager(
                        sm.Secret.from_secret_attributes(self, "secret_key",
                            secret_complete_arn="arn:aws:secretsmanager:us-east-1:614871946825:secret:token-secret-key-zK8E2a",
                        )
                    )
                },
                # add permission to get SQS queue url and send messages to SQS queue
                task_role=role
            ),
            memory_limit_mib=1024,
            cpu=256,
        )
