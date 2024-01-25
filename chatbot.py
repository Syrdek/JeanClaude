# pip install llama-cpp-python
import html
import json
import re
import logging

import pybars
from llama_cpp import Llama

# https://huggingface.co/TheBloke/Llama-2-7b-Chat-GGUF
# https://huggingface.co/TheBloke/Llama-2-13B-chat-GGUF


class ChatBot(object):

    def __init__(self, name="jeanclaude",
                 model_path="/data/llama2/llama-2-13b-chat.Q4_K_S.gguf",
                 max_prompt=512,
                 preprompt="",
                 preprompt_template="<s>[INST] <<SYS>>\n{{preprompt}}\n<</SYS>>\n\n{{#each messages}}{{#ifUser}}{{content}} [/INST] {{/ifUser}}{{#ifAssistant}}{{content}} </s><s>[INST] {{/ifAssistant}}{{/each}}",
                 stopwords=["\n"],
                 max_ctx=8192):
        self.name = name
        self.stopwords = stopwords
        self.max_prompt = max_prompt
        logging.info(f"Chargement du modele llama {model_path} pour {name}")
        self.llm = Llama(model_path=model_path, n_ctx=8192, verbose=False)
        self.preprompt = preprompt % {"name": name}
        self.preprompt_template = pybars.Compiler().compile(preprompt_template)

    def promptify(self, context) -> str:
        return self.__promptify(context)

    def __promptify(self, context)->str:
        text_size = 0
        data = {
            "name": self.name,
            "preprompt": self.preprompt,
            "messages": []
        }

        for msg in reversed(context):
            text_size = text_size + len(msg["message"])
            if text_size > self.max_prompt and len(data["messages"]) > 0:
                logging.info(f"Le nombre max de caracteres de contexte est depasse ({text_size} > {self.max_prompt}). Le contexte sera tronque.")
                break

            line = {
                "content": msg["message"],
                "user": msg["user"],
                "ifUser": True,
                "ifAssistant": False
            }

            replace_chars_ptn = "[^0-9a-zA-Z]"
            if re.sub(replace_chars_ptn, "", msg["user"]).lower() == re.sub(replace_chars_ptn, "", self.name).lower():
                line["ifUser"] = False
                line["ifAssistant"] = True

            data["messages"] = [line] + data["messages"]

        return html.unescape(self.preprompt_template(data))

    @staticmethod
    def __format_response(context, response):
        last_context = context[-1]
        result = {"message": response["choices"][0]["text"]}

        if "channel_id" in last_context:
            result["channel_id"] = last_context["channel_id"]

        if "id" in last_context:
            result["root_id"] = last_context["id"]

        return result

    def ask(self, message, max_tokens=4096):
        prompt = self.__promptify(context=message)
        logging.info(f"Demande formattee : {prompt}")
        text = self.llm(prompt, max_tokens=max_tokens, stop=self.stopwords)["choices"][0]["text"]
        text = text.strip()
        if text.lower().startswith("gpt4"):
            text = text[4:].strip()
        if text.lower().startswith(self.name.lower()):
            text = text[len(self.name):].strip()
        if text.lower().startswith(":"):
            text = text[1:].strip()
        return text


if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)

    chatbot = ChatBot(name=config["chatbot"]["name"],
            model_path=config["chatbot"]["model_path"],
            max_prompt=config["chatbot"]["max_prompt"],
            preprompt=config["chatbot"]["preprompt"],
            preprompt_template=config["templates"][config["chatbot"]["template"]],
            stopwords=config["chatbot"]["stopwords"])

    messages = [
        {"user": "Roméo", "message":"I am working on a prime numbers generator."},
        {"user": "Cédric", "message":"Could you write a small python function that returns true if a number is prime ?"},
        {"user": "JeanClaude", "message": "Of course! Here's a simple function that should do what you're looking for:\n```\ndef is_prime(n):\n    return not any(n % x == 0 for x in range(2, int(n ** 0.5) + 1))\n```\nLet me know if you have any questions or need further assistance!\n"},
        {"user": "Francis", "message": "Could you write it in java too ?", "channel_id": "CHANNEL"}
    ]
    print(chatbot.promptify(messages))
    print(chatbot.ask(messages))

"""
[
{"user":"user", "message":"Could you write a small python function that returns true if a number is prime ?"},
{"user":"JeanClaude", "message": "Of course! Here's a simple function that should do what you're looking for:\n```\ndef is_prime(n):\n    return not any(n % x == 0 for x in range(2, int(n ** 0.5) + 1))\n```\nLet me know if you have any questions or need further assistance!\n", "index": 0, "logprobs": null, "finish_reason": "stop"},
{"user":"user", "message":"Could you write it in java too ?", "channel_id":"CHANNEL"}
]
"""

