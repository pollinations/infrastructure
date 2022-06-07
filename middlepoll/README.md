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
python middlepoll/main.py --aws_endpoint http://localhost:4566 --aws_profile localstack 
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

curl -H "Accept: application/json" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.IAsdG_P_c8SRPM4pniTaFypMq6v2zwTIDjqMgmlBh3o" \
    Infra-beecl-PWALVC2Z2YD3-913041626.us-east-1.elb.amazonaws.com/me/

docker run -d -p 5000:5000 r8.im/orpatashnik/styleclip@sha256:b6568e6bebca9b3f20e7efb6c710906efeb2d1ac6574a7a9d350fa51ee7daec4
curl http://localhost:5000/predict -X POST \
  -F input=@man.jpg \
  -F neutral="a man" \
  -F target="a man with a hat" \
  -F manipulation_strength=4.1 \
  -F disentanglement_threshold=0.15 
```



