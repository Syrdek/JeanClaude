import logging
import os
import re

from diffusers import StableDiffusionPipeline
import json
import torch
import unicodedata
import sys

import numpy as np
import torch.nn as nn
from transformers import CLIPConfig, CLIPVisionModel, PreTrainedModel

# install torch for cuda :
# pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
# https://pytorch.org/get-started/locally/

# install torch for cpu :
# pip3 install torch torchvision torchaudio

# remove security checks in safety_checker.py


def strip_accents(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')

class StableDiff(object):
    def __init__(self, model_path="model_dir", model_id="runwayml/stable-diffusion-v1-5", save_path=None, allow_nsfw=False):
        self.save_path = save_path
        self.use_cuda = torch.cuda.is_available()

        logging.info(f"Chargement de StableDiffusion [cuda={self.use_cuda}]...")
        pipeline_args = {}

        if allow_nsfw:
            pipeline_args["safety_checker"] = None
            pipeline_args["requires_safety_checker"] = False
            # voir safety-checker

        if self.use_cuda:
            pipeline_args["torch_dtype"] = torch.float16

        self.stable = StableDiffusionPipeline.from_pretrained(
            model_id,
            cache_dir=model_path,
            **pipeline_args).to("cuda" if self.use_cuda else "cpu")


    def ask(self, prompt):
        logging.info(f"Stable diffusion prompt : {prompt}")
        prompt = strip_accents(prompt)
        safe_prompt = re.sub("[^0-9a-zA-Z_.-]", "", re.sub(" ", "_", prompt)).lower()
        res = self.stable(prompt)
        i = res.images[0]
        nsfw = res.nsfw_content_detected[0]

        if self.save_path:
            if nsfw:
                safe_prompt = f"NSFW_{safe_prompt}"
            save_path = os.path.abspath(self.save_path.replace("{prompt}", safe_prompt))
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            i.save(save_path)

        if nsfw:
            logging.warning(f"Un contenu NSFW a ete genere en reponse a : {safe_prompt}")

        return safe_prompt, i, nsfw


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    with open("config.json", "r") as f:
        config = json.load(f)

    stable = StableDiff(
            model_path=config["stablediff"]["model_path"],
            model_id=config["stablediff"]["model_id"],
            save_path=config["stablediff"]["save_path"])

    if len(sys.argv) > 0:
        for arg in sys.argv[1:]:
            stable.ask(arg)
    else:
        stable.ask("A duck flying in the sky over Paris")
