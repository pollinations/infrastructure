import os


stage = "prod" if os.environ.get("STAGE") == "prod" else "dev"
queue_name = f"pollens-queue-{stage}"