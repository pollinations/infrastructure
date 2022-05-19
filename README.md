# middlepoll

Middleware for workers with replicate containers:
[] accepts requests from load balancer
[] does whatever middleware we want
    [] log pollen to central db
    [x] authentication
[] forward request to another container


# CI
- build dockerfile
- push to ecr
- update task definition

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
python middlepoll/main.py
```
Or build an run the image:
```
docker build -t middleware .
docker run -p 8000:5000 --env-file .env middleware
```
# Requests
```
curl -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.ealNyCRtZ0DDJWmexGomcWQll-57wsfMuL06J7MRVts" \
    localhost:5555/me/
```

