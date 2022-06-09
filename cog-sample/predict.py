# Prediction interface for Cog ⚙️
# https://github.com/replicate/cog/blob/main/docs/python.md

import os
import time
from locale import strcoll
from typing import Iterator

from cog import BasePredictor, File, Input, Path


class Predictor(BasePredictor):
    def setup(self):
        """Load the model into memory to make running multiple predictions efficient"""
        # self.model = torch.load("./weights.pth")
        pass

    def predict(self, prompt: str = Input("prompt")) -> Iterator[str]:
        """Run a single prediction on the model"""
        for i in range(10):
            with open(f"/src/output/{i}.txt", "w") as f:
                f.write(prompt)
            yield str(i) + prompt
            time.sleep(3)
        # processed_input = preprocess(image)
        # output = self.model(processed_image, scale)
        # return postprocess(output)
