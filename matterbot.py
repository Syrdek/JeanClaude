#!/opt/matterbot/venv/bin/python
import json
import logging
import logging.config
import io
import time

from mattermostdriver import Driver
from horoscope import Horoscopper
from chatbot import ChatBot
from stablediff import StableDiff
from taskqueue import TaskQueue

# https://api.mattermost.com/#tag/posts/operation/GetPostsForChannel
# https://api.mattermost.com/#tag/posts/operation/CreatePost
# https://api.mattermost.com/#tag/posts/operation/GetPost

'''
Browses a json object.
'''
def jsget(js, *args):
    cursor = js
    for elt in args:
        if isinstance(cursor, list):
            i = int(elt)
            if len(cursor) > i:
                cursor = cursor[i]
            else:
                return None
        elif isinstance(cursor, dict):
            if elt in cursor:
                cursor = cursor.get(elt)
            else:
                return None
    return cursor


def current_milli_time():
    return round(time.time() * 1000)


class MatterBot(object):
    command_prefix = "!"
    clear_context_command = f"{command_prefix}clear"
    horoscope_context_command = f"{command_prefix}horoscope"
    imagine_context_command = f"{command_prefix}imagine"

    def __init__(self, host='mattermost.dune.thales', port=80, token='e3h8r7t7yir73xy7z7jdfjsehe', scheme='http', max_context=10, use_threads=True):
        self.driver = Driver({'url': host, 'port': port, 'token': token, 'scheme': scheme})
        self.driver.login()
        self.chatbot = ChatBot(name=config["chatbot"]["name"],
                               model_path=config["chatbot"]["model_path"],
                               max_prompt=config["chatbot"]["max_prompt"],
                               preprompt=config["chatbot"]["preprompt"],
                               preprompt_template=config["templates"][config["chatbot"]["template"]],
                               stopwords=config["chatbot"]["stopwords"])
        self.stable = StableDiff(
            model_path=config["stablediff"]["model_path"],
            model_id=config["stablediff"]["model_id"],
            save_path=config["stablediff"]["save_path"],
            allow_nsfw=config["stablediff"]["allow_nsfw"])
        self.use_threads = use_threads
        self.max_context = max_context
        self.me = self.driver.users.get_user("me")
        self.at_me_prefix = f"@{self.me['username']}"
        self.tasks_queue = TaskQueue()

        logging.info("Ready !")

    '''
    Start the websocket
    '''
    def run(self):
        logging.info("Setting up websocket")
        while True:
            self.driver.init_websocket(self.event_handler)
            logging.info("Websocket disconnected, reconnecting...")

    '''
    Tells if a message is a command.
    '''
    def is_command(self, message):
        return message.strip().startswith(self.command_prefix)

    '''
    Tells if a message was sent by the bot.
    '''
    def is_from_me(self, event):
        return jsget(event, "data", "post", "user_id") == self.me["id"]\
            or jsget(event, "data", "post", "sender_name") == self.me["username"]

    '''
    Tells if a message is for the bot.
    '''
    def is_personal_message(self, event: dict) -> bool:
        return "D" == jsget(event, "data", "channel_type")\
            or str(jsget(event, "data", "post", "message")).startswith(self.at_me_prefix)

    def remove_personal_prefix(self, message: str) -> str:
        message = message.strip()
        if message.startswith(self.at_me_prefix):
            return message[len(self.at_me_prefix):].strip()
        return message

    '''
    Collects the messages that occurred before the one given.
    '''
    def get_message_context(self, event: dict, message: str, nb_messages: int = None) -> list:
        channel_id = jsget(event, "data", "post", "channel_id")
        post_id = jsget(event, "data", "post", "id")

        previous_posts = self.driver.posts.get_posts_for_channel(channel_id, {"per_page": self.max_context, "before": post_id})
        context = [
            {"user": jsget(event, "data", "sender_name").lstrip("@"), "message": message}
        ]

        for key in previous_posts["order"]:
            post = previous_posts["posts"][key]
            post_message = self.remove_personal_prefix(jsget(post, "message"))

            if post_message.lower().startswith(MatterBot.clear_context_command):
                # On ne recupere pas le contexte au-delà de '!clear'
                break
            elif post_message.lower().startswith(MatterBot.command_prefix):
                continue

            user_name = self.driver.users.get_user(post["user_id"])["username"]
            context.insert(0, {"user": user_name.lstrip("@"), "message": post_message})

        return context

    '''
    Notified when a command is invoked.
    '''
    def on_command(self, event: dict, message: str):
        channel = jsget(event, "data", "post", "channel_id")
        logging.info(f"Got command message on {channel}: {message}")
        if message.startswith(MatterBot.horoscope_context_command):
            for msg in Horoscopper(proxies=config["proxies"], **config["horoscope"]).collect():
                self.driver.posts.create_post({"channel_id": channel, "message": msg})
        elif message.startswith(MatterBot.imagine_context_command):
            self.tasks_queue.add_task(self.imagine,
                                      message=message[len(MatterBot.imagine_context_command):].strip(),
                                      channel_id=channel)

    '''
    Notified when a stablediffusion is invoked.
    '''
    def imagine(self, message: str, channel_id: str, thread_root: str = None):
        logging.info(f"There are {len(self.tasks_queue) + 1} tasks queued")
        filename, image, nsfw = self.stable.ask(message)

        response = {
            "channel_id": channel_id,
            "message": f"Pour '{message}', j'imagine ça :"
        }

        if self.use_threads and thread_root is not None and thread_root != "":
            response["root_id"] = thread_root

        if nsfw:
            response["message"] = f"Je détecte un contenu non autorisé dans l'image que j'ai construite pour {message}. Je ne vais donc pas l'envoyer.\nSi c'est une erreur, vous pouvez me redemander la même image."
        else:
            imageio = io.BytesIO()
            image.save(imageio, format='PNG')

            file_id = self.driver.files.upload_file(
                channel_id=channel_id,
                files={'files': (f"{filename}.png", imageio.getvalue())}
            )['file_infos'][0]['id']

            response["file_ids"] = [file_id]

        self.driver.posts.create_post(response)

    '''
    Respond to a message.
    '''
    def respond(self, context: dict, channel_id: str, thread_root: str = None):
        logging.info(f"There are {len(self.tasks_queue) + 1} tasks queued")
        chat_text = self.chatbot.ask(context, max_tokens=config["chatbot"]["max_tokens"])
        logging.info(f"Response to {json.dumps(context, indent=2)} was : {chat_text}")
        response = {"channel_id": channel_id, "message": chat_text}
        if self.use_threads and thread_root is not None and thread_root != "":
            response["root_id"] = thread_root
        try:
            self.driver.posts.create_post(response)
        except:
            del response["root_id"]
            self.driver.posts.create_post(response)

    '''
    Notified when a message is posted.
    '''
    def on_post_received(self, event: dict) -> dict:
        post = json.loads(jsget(event, "data", "post"))
        event["data"]["post"] = post

        if not self.is_from_me(event):
            message = jsget(post, 'message')
            if message.startswith(self.at_me_prefix):
                message = message[len(self.at_me_prefix):].strip()

            if self.is_command(message):
                self.on_command(event, message)

            elif self.is_personal_message(event):
                logging.info(f"Got personal message on {post['channel_id']} : {message}")
                root_id = jsget(post, "root_id")
                if root_id == "" or root_id is None:
                    root_id = jsget(post, "id")
                context = self.get_message_context(event=event, message=message)
                self.tasks_queue.add_task(self.respond, context=context, channel_id=post["channel_id"], thread_root=root_id)

        return event

    '''
    Notified when any message is received from the websocket.
    https://api.mattermost.com/#tag/WebSocket
    '''
    async def event_handler(self, message: str):
        try:
            event = json.loads(str(message))
            event_type = event.get('event')
            logging.debug(f"Event received : {event}")

            if event_type == "posted":
                self.on_post_received(event)

        except:
            logging.exception(f"Failed to process event {message}")


if __name__ == '__main__':
    try:
        logging_conf_path = "logging.json"
        app_conf_path = "config.json"
        with open(logging_conf_path, "r") as f:
            logging.config.dictConfig(json.load(f))

        with open(app_conf_path, "r") as f:
            config = json.load(f)

        logging.info("Chargement de matterbot...")
        matterbot = MatterBot(**config["mattermost"])
        matterbot.run()
    except:
        logging.exception("Echec de lancement de l'application")
