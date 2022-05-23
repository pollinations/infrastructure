# pollinator
- Read tasks from an SQS queue 
- execute tasks
- stream outputs to topic specified in queue item

# Run locally
Install package:
```sh
# Install dependencies
pip install -e ".[test]"

# Install pre-commit hooks
brew install pre-commit
pre-commit install -t pre-commit
```
and run the server:
```
python pollinator/main.py
```
Or build an run the image:
```
docker build -t pollinator .
docker run -p 8000:5000 --env-file .env pollinator
```
# Requests



