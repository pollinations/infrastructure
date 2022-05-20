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
    aws_autoscaling as autoscaling,
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


        cluster = ecs.Cluster(self, "gpu-cluster",
            vpc=vpc
        )

        auto_scaling_group = autoscaling.AutoScalingGroup(self, "models-scaling-group",
            vpc=vpc,
            instance_type=ec2.InstanceType("g4dn.xlarge"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(hardware_type=ecs.AmiHardwareType.GPU), # amzn2-ami-ecs-gpu-hvm-2.0.20220509-x86_64-ebs
            
            min_capacity=1,
            max_capacity=2
        )

        capacity_provider = ecs.AsgCapacityProvider(self, "AsgCapacityProvider",
            auto_scaling_group=auto_scaling_group
        )
        cluster.add_asg_capacity_provider(capacity_provider)

        # task_definition = ecs.Ec2TaskDefinition(self, "TaskDef")

        # task_definition.add_container("web",
        #     image=ecs.ContainerImage.from_registry(
        #         "r8.im/orpatashnik/styleclip@sha256:b6568e6bebca9b3f20e7efb6c710906efeb2d1ac6574a7a9d350fa51ee7daec4e"
        #     ),
        #     memory_reservation_mi_b=14000
        # )



        # # Create EC2 based GPU cluster for scheduled tasks
        queue_processing_ec2_service = ecs_patterns.QueueProcessingEc2Service(self, "Service",
            cluster=cluster,
            image=ecs.ContainerImage.from_registry("r8.im/orpatashnik/styleclip@sha256:b6568e6bebca9b3f20e7efb6c710906efeb2d1ac6574a7a9d350fa51ee7daec4"),
            # command=["echo", "$1 $2 $3 $4 $5 $6"],
            enable_logging=True,
            gpu_count=1,
            environment={},
            max_scaling_capacity=5,
            container_name="styleclip-cog",
            memory_limit_mib=14000
            # memory_limit_mi_b=14000,
        )

        # Create cluster for models
        # ecs_scheduled_task = ecs_patterns.ScheduledEc2Task(self, "ScheduledTask",
        #     cluster=cluster,
        #     scheduled_ec2_task_image_options=ecs_patterns.ScheduledEc2TaskImageOptions(
        #         image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample"),
        #         memory_limit_mi_b=256,
        #         environment={}
        #     ),
        #     schedule=ecs_patterns.ScheduledEc2Task(,
        #     enabled=True,
        #     rule_name="sample-scheduled-task-rule"
        # )

