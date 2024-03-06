import os
import gradio as gr
import copy
import time
import llama_cpp
from llama_cpp import Llama
import json
import sys
import logging
import logging.config


model_path = "/data/dolphin-2.5-mixtral-8x7b.Q4_K_M.gguf"
model_path = "/data/dolphin-2.6-mistral-7b-dpo-laser.Q4_K_M.gguf"
stop_words = ["<|im"]

def deepseek_instruct_format(message, history):
    input_prompt = """
Vous êtes un expert développeur IA, utilisant Le modèle de code DeepSeek.
Vous répondez toujours aux questions posées de la manière la plus complète possible.
Si une question ne fait pas sens ou n'est pas cohérente, expliquez pourquoi au lieu de répondre à quelque chose qui n'est pas correct.
"""
# Deepseek ne prend pas correctement en compte l'historique
#    for interaction in history:
#        input_prompt = f"""
#### Instruction:
#{interaction[0]}
#### Response:
#{interaction[1]}
#"""
    return f"""{input_prompt}
### Instruction:
{message}
### Response:
"""

def chatml_format(message, history):
    preprompt = """
Vous êtes un assistant serviable, respectueux et honnête.
Vous répondez toujours aux questions posées de la manière la plus complète possible.
Si une question ne fait pas sens ou n'est pas cohérente, expliquez pourquoi au lieu de répondre à quelque chose qui n'est pas correct.
"""
    input_prompt = f"<|im_start|>system\n{preprompt}<|im_end|>\n"
    for interaction in history:
        input_prompt = f"{input_prompt}<|im_start|>user\n{interaction[0]}<|im_end|><|im_start|>assistant\n{interaction[1]}\n<|im_end|>\n"

    return f"{input_prompt}<|im_start|>user\n{message}<|im_end|><|im_start|>assistant\n"


def generate_text(message, history):
    fmt = model_format(message=message, history=history)
    logging.info(f"Demande de prediction : \n{fmt}")
    output = llm(
        fmt,
        temperature=0.15,
        top_p=0.1,
        top_k=40,
        repeat_penalty=1.1,
        #max_tokens=16,
        max_tokens=16384,
        stop=stop_words,
        stream=True,
    )

    temp = ""
    for out in output:
        stream = copy.deepcopy(out)
        temp += stream["choices"][0]["text"]
        yield temp

    logging.info(f"Reponse : \n{temp}")


if __name__ == '__main__':
    try:
        if len(sys.argv) > 1:
            model_path = sys.argv[1]

        if "deepseek" in model_path:
            model_format = deepseek_instruct_format
            stop_words = ["### Instruction", "### Response" ]
        else:
            model_format = chatml_format
            stop_words = ["<|im"]
    
        logging.basicConfig(
                level=logging.INFO,
                format="[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s",
                filename="/var/log/matterbot/gradio.log")
        logging.info("Loading LLM...")

        llm = Llama(
            model_path=model_path,
            n_ctx=32768
        )

        history = []

        logging.info("Loading Gradio...")

        demo = gr.ChatInterface(
            generate_text,
            title="Llama2 chatbox",
            description="Chatbox",
            examples=["Ecris une fonction java qui indique si un nombre donné en paramètre est premier"],
            retry_btn=None,
            undo_btn="Delete",
            clear_btn="Clear"
        )

        logging.info("Launching gradio...")
        
        demo.launch(share=False,
            server_name="0.0.0.0",
            server_port=7890)

    except:
        logging.exception("Echec de lancement de l'application")



