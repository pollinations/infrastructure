import os
import subprocess
import time
import tempfile
import json
import shutil
import requests

from pollinator.constants import images

def debug(f):
    def debugged(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            print(type(e), e)
            breakpoint()
            f(*args, **kwargs)
    return debugged


# @debug
def process_message(message):
    # start process: pollinate --send --ipns --nodeid nodeid --path /content/ipfs

    # Prepare output folder
    output_path = "outputs"
    shutil.rmtree(output_path, ignore_errors=True)
    os.makedirs(output_path, exist_ok=True)

    # # Start IPFS syncinv=g
    # ipfs_pid = subprocess.Popen(
    #     f"pollinate --send --ipns --nodeid {message['pollen_id']}"
    #     f" --path {output_path} ",
    #     shell=True).pid

    # process message
    image = images[message['notebook']]
    gpus = "" if True else "--gpus all" # TODO check if GPU is available
    # Start cog container
    cog_cmd = (
        'docker run --rm --detach --cidfile /tmp/cidfile --publish 5000:5000'
        f'--mount type=bind,source="$(pwd)"/output,target=/src/output'
        f'{gpus} {image}'
    )
    print(cog_cmd)
    os.system(cog_cmd)

    # Send request to cog container
    payload = {
        "inputs": message['inputs']
    }  
    response = requests.post("http:localhost:5000/predictions", json=payload)

    if response.status_code != 200:
        print(response.content)
        with open(f"{output_path}/error.txt", "w") as f:
            f.write(response.text)
    # Kill cog container
    container_id = open("/tmp/cidfile").read()
    os.system(f"docker kill {container_id}")
    # # kill pollinate
    # time.sleep(5)
    # subprocess.Popen(["kill", str(ipfs_pid)])