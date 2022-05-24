import os
import subprocess
import time
import tempfile

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

    # with tempfile.TemporaryDirectory() as output_path:
    if True:
        output_path = message['pollen_id']
        # ipfs_pid = subprocess.Popen(
        #     f"pollinate --send --ipns --nodeid {message['pollen_id']}"
        #     f" --path {output_path} ",
        #     shell=True).pid
        # process message
        image = images[message['notebook']]

        cog_cmd = (
            f'cog predict {image}'
            # f' -i prompts="{message["prompt"]}"'
            # ' -i drawer="vqgan"'
            ' -i prompt="yo"'
        )
        print(cog_cmd)
        os.system(cog_cmd)
        # kill pollinate
        time.sleep(5)
        # subprocess.Popen(["kill", str(ipfs_pid)])