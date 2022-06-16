import os


stage = "prod" if os.environ.get("STAGE") == "prod" else "dev"
queue_name = f"pollens-queue-{stage}"

certificate_arn = "arn:aws:acm:us-east-1:614871946825:certificate/e363dfb7-2c07-4a4e-88fc-c61d97417ef2"