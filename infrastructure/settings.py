import os


stage = "prod" if os.environ.get("STAGE") == "prod" else "dev"
queue_name = f"pollens-queue-{stage}"

certificate_arn = "arn:aws:acm:us-east-1:614871946825:certificate/226b3e6a-612f-449a-ae71-5d45648246f1"