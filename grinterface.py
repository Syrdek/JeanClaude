import os
import gradio as gr
import copy
import time
import llama_cpp
from llama_cpp import Llama
import json
import logging
import logging.config


def chatml_format(message, history):
    input_prompt = f"<|im_start|>system\n{preprompt}<|im_end|>\n"
    for interaction in history:
        input_prompt = f"{input_prompt}<|im_start|>user\n{interaction[0]}<|im_end|><|im_start|>assistant\n{interaction[1]}\n<|im_end|>\n"

    return f"{input_prompt}<|im_start|>user\n{message}<|im_end|><|im_start|>assistant\n"


model_path = "/data/dolphin-2.5-mixtral-8x7b.Q4_K_M.gguf"
preprompt = """
You are a helpful, respectful and honest assistant. Always answer as helpfully as possible, while being safe.  Your answers should not include any harmful, unethical, racist, sexist, toxic, dangerous, or illegal content. Please ensure that your responses are socially unbiased and positive in nature.
If a question does not make any sense, or is not factually coherent, explain why instead of answering something not correct. If you don't know the answer to a question, please don't share false information.
"""

def generate_text(message, history):
    input_prompt = chatml_format(message=message, history=history)

    output = llm(
        input_prompt,
        temperature=0.15,
        top_p=0.1,
        top_k=40, 
        repeat_penalty=1.1,
        max_tokens=4096,
        stop=[
            "<|im",
        ],
        stream=True,
    )

    temp = ""
    for out in output:
        stream = copy.deepcopy(out)
        temp += stream["choices"][0]["text"]
        yield temp


if __name__ == '__main__':
    try:
        app_conf_path = "config.json"

        with open(app_conf_path, "r") as f:
            config = json.load(f)

        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            chat_format="chatML"
        )

        history = []

        demo = gr.ChatInterface(
            generate_text,
            title="Llama2 chatbox",
            description="Chatbox",
            examples=["tell me everything about llamas"],
            retry_btn=None,
            undo_btn="Delete Previous",
            clear_btn="Clear"
        )
        #demo.queue(concurrency_count=1, max_size=5)
        demo.launch(share=False,
            server_name="0.0.0.0",
            server_port=7890)

    except:
        logging.exception("Echec de lancement de l'application")



