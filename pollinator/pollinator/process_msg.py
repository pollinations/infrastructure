import os

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


@debug
def process_message(message):
    # start process: pollinate --send --ipns --nodeid nodeid --path /content/ipfs 

    # process message
    # kill pollinate
    print("message", type(message))
    image = images[message['notebook']]
    os.system(
        f'cog predict {image}'
        f' -i prompts="{message["prompt"]}"'
        ' -i drawer="vqgan"'
        f' --output=outputs/{message["pollen_id"]}'
    )
    return