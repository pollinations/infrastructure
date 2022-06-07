import secrets
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


with open("./user_data.sh") as f:
    user_data = f.read()
class InfrastructureStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC and Subnets for the ECS Cluster
        vpc = ec2.Vpc(self, "VPC",
                        max_azs=3,
                    )

        # Create EC2 machines for pollinator
        role = iam.Role(self, "PollinatorRole",
            assumed_by=iam.ServicePrincipal("sns.amazonaws.com")
        )
        role.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=["sqs:*"]
        ))
        role.add_to_policy(iam.PolicyStatement(
            resources=["*"],
            actions=["ecr:*"]
        )) 

        security_group = ec2.SecurityGroup(self, "PollinatorSecurityGroup",
                vpc=vpc,
                allow_all_outbound=True)
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "SSH")
        security_group.add_ingress_rule(ec2.Peer.any_ipv6(), ec2.Port.tcp(22), "SSH")
        
        pollinator_ec2 = ec2.Instance(self, "PollinatorEC2",
            instance_type=ec2.InstanceType("g4dn.xlarge"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(hardware_type=ecs.AmiHardwareType.GPU), 
            key_name="pollinations-aws-key",
            role=role,
            vpc=vpc,
            user_data=ec2.UserData.custom(user_data),
            # add public IP
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            # add security group
            security_group=security_group,
        )
        # Add log group to cloudwatch
        log_group = logs.LogGroup(self, "PollinatorLogGroup",
            retention=logs.RetentionDays.ONE_WEEK,
        )
        log_group.grant_write(iam.ServicePrincipal("ec2.amazonaws.com"))

        pollinator_ec2.instance.add_property_override("BlockDeviceMappings", [{
            "DeviceName": "/dev/xvda",
            "Ebs": {
                "VolumeSize": "150",
                "VolumeType": "gp3",
                "Iops": "3000",
                "DeleteOnTermination": "true"
            }
        }])

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
