Sample cog image that runs on cpu

Usage:
```
cd cog-sample
cog build -t cog-sample
cog predict cog-sample -i input=hi
```

Or:
```
cd cog-sample
cog build -t cog-sample

docker run -d -p 5000:5000 cog-sample

curl http://localhost:5000/predict -X POST \
  -F prompt="an avocado made of armchairs"
```