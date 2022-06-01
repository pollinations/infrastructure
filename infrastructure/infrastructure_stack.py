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


instance_type = "GPU"

class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC and Subnets for the ECS Cluster
        vpc = ec2.Vpc(self, "VPC",
                        max_azs=3,
                    )

        cluster = ecs.Cluster(self, "gpu-cluster",
            vpc=vpc
        )


        if instance_type == "GPU":
            auto_scaling_group = autoscaling.AutoScalingGroup(self, "models-scaling-group",
                vpc=vpc,
                instance_type=ec2.InstanceType("g4dn.xlarge"),
                machine_image=ecs.EcsOptimizedImage.amazon_linux2(hardware_type=ecs.AmiHardwareType.GPU), # amzn2-ami-ecs-gpu-hvm-2.0.20220509-x86_64-ebs
                min_capacity=1,
                max_capacity=2,
                key_name="pollinations-aws-key",
            )
            gpu_count = 1
            memory_limit_mib = 14000
        else:
            auto_scaling_group = autoscaling.AutoScalingGroup(self, "models-scaling-group",
                vpc=vpc,
                instance_type=ec2.InstanceType("t2.medium"),
                machine_image=ecs.EcsOptimizedImage.amazon_linux2(), # amzn2-ami-ecs-gpu-hvm-2.0.20220509-x86_64-ebs
                min_capacity=1,
                max_capacity=2
            )
            gpu_count = 0
            memory_limit_mib = 1024

        capacity_provider = ecs.AsgCapacityProvider(self, "AsgCapacityProvider",
            auto_scaling_group=auto_scaling_group
        )
        cluster.add_asg_capacity_provider(capacity_provider)

        image = ecs.ContainerImage.from_asset(directory=os.path.join(".", "pollinator"), build_args={"platform": "linux/amd64"})
        # # Create EC2 based GPU cluster for scheduled tasks
        queue_processing_ec2_service = ecs_patterns.QueueProcessingEc2Service(self, "Service",
            cluster=cluster,
            image=image,
            enable_logging=True,
            gpu_count=gpu_count,
            max_scaling_capacity=5,
            container_name="pollinator",
            memory_limit_mib=memory_limit_mib,
            # set environment variable to the queue url
        )

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
                    "QUEUE_NAME": queue_processing_ec2_service.sqs_queue.queue_name,
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
