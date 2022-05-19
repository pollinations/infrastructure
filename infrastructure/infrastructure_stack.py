from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    aws_s3 as s3,
    aws_s3_notifications as s3_notifications,
    aws_sns as sns,
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
)
from aws_cdk.aws_ecr_assets import DockerImageAsset
from constructs import Construct
import os

class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC and Subnets for the ECS Cluster
        vpc = ec2.Vpc(self, "VPC",
                        max_azs=3,
                    )

        image = ecs.ContainerImage.from_asset(directory=os.path.join(".", "middlepoll"), build_args={"platform": "linux/amd64"})

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
                    # "secret_key": "not the real key"
                },
                secrets={
                    "secret_key": ecs.Secret.from_secrets_manager(
                        sm.Secret.from_secret_attributes(self, "secret_key",
                            secret_complete_arn="arn:aws:secretsmanager:us-east-1:614871946825:secret:token-secret-key-zK8E2a",
                        )
                    )
                }
            ),
            memory_limit_mib=1024,
            cpu=256,
        )

        # Create Services for each model
        

