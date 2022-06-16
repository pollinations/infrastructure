import os
import secrets

from aws_cdk import Stack
from aws_cdk import aws_autoscaling as autoscaling
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_elasticloadbalancingv2 as elb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3  # Duration,; aws_sqs as sqs,
from aws_cdk import aws_s3_notifications as s3_notifications
from aws_cdk import aws_secretsmanager as sm
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as sns_subscriptions
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_certificatemanager as certificatemanager
from aws_cdk.aws_ecr_assets import DockerImageAsset
from aws_cdk import aws_route53 as route53
from constructs import Construct

from infrastructure import settings

with open("./user_data.sh") as f:
    user_data = f.read().replace("$QUEUE_NAME", settings.queue_name)

instance_type = "GPU"


class InfrastructureStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC and Subnets for the ECS Cluster
        vpc = ec2.Vpc(
            self,
            "VPC",
            max_azs=3,
        )

        # Create SQS queue
        sqs_queue = sqs.Queue(self, "SQSQueue", queue_name=settings.queue_name)

        # Create EC2 machines for pollinator
        role = iam.Role(
            self, "PollinatorRole", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )
        role.add_to_policy(iam.PolicyStatement(resources=["*"], actions=["sqs:*"]))
        role.add_to_policy(iam.PolicyStatement(resources=["*"], actions=["ecr:*"]))
        role.add_to_policy(
            iam.PolicyStatement(
                resources=["*"],
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                    "logs:DescribeLogStreams",
                ],
            )
        )

        
        security_group = ec2.SecurityGroup(
            self, "PollinatorSecurityGroup", vpc=vpc, allow_all_outbound=True
        )
        security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "SSH")
        security_group.add_ingress_rule(ec2.Peer.any_ipv6(), ec2.Port.tcp(22), "SSH")

        auto_scaling_group = autoscaling.AutoScalingGroup(
            self,
            "models-scaling-group",
            vpc=vpc,
            instance_type=ec2.InstanceType(
                "g4dn.xlarge" if instance_type == "GPU" else "t2.medium"
            ),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(
                hardware_type=ecs.AmiHardwareType.GPU
            ),  # amzn2-ami-ecs-gpu-hvm-2.0.20220509-x86_64-ebs
            min_capacity=1,
            max_capacity=2,
            key_name="pollinations-aws-key",
            user_data=ec2.UserData.custom(user_data),
            associate_public_ip_address=True,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            role=role,
            security_group=security_group,
            block_devices=[
                autoscaling.BlockDevice(
                    device_name="/dev/xvda",
                    volume=autoscaling.BlockDeviceVolume.ebs(
                        150, iops=3000, volume_type=autoscaling.EbsDeviceVolumeType.GP3
                    ),
                )
            ]
        )

        # Add log group to cloudwatch
        log_group = logs.LogGroup(
            self,
            "PollinatorLogGroup",
            retention=logs.RetentionDays.ONE_WEEK,
        )

        # Create middleware ecs cluster
        image = ecs.ContainerImage.from_asset(
            directory=os.path.join(".", "middlepoll"),
            build_args={"platform": "linux/amd64"},
        )

        role = iam.Role(
            self,
            "FargateContainerRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )
        role.add_to_policy(iam.PolicyStatement(actions=["sqs:*"], resources=["*"]))

        certificate_arn = "arn:aws:acm:us-east-1:614871946825:certificate/27072bfb-9146-4fc1-b380-bb92521004a7"
        certificate = certificatemanager.Certificate.from_certificate_arn(self, "pollinationsworker", certificate_arn)

        # Create ECS pattern for the ECS Cluster
        cluster = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "bee-cluster",
            vpc=vpc,
            # security_group=ec2.SecurityGroup(self, "SecurityGroup", vpc=vpc),
            public_load_balancer=True,
            protocol=elb.ApplicationProtocol.HTTPS,
            certificate=certificate,
            redirect_http=True,
            # # domain_name=f"worker-{settings.stage}.pollinations.ai",
            # # domain_zone=route53.HostedZone.from_lookup(self, "DomainZone", domain_name="pollinations.ai"),
            desired_count=1,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=image,
                container_port=5000,
                environment={
                    "DEBUG": "True",
                    "LOG_LEVEL": "DEBUG",
                    "LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "QUEUE_NAME": settings.queue_name,
                },
                secrets={
                    "secret_key": ecs.Secret.from_secrets_manager(
                        sm.Secret.from_secret_attributes(
                            self,
                            "secret_key",
                            secret_complete_arn="arn:aws:secretsmanager:us-east-1:614871946825:secret:token-secret-key-zK8E2a",
                        )
                    )
                },
                # add permission to get SQS queue url and send messages to SQS queue
                task_role=role,
            ),
            memory_limit_mib=1024,
            cpu=256,
        )
