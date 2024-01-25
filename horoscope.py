import sys
import json
import typing
import requests
from lxml import html
import urllib3

urllib3.disable_warnings()


class Horoscopper(object):
    def __init__(self, signes: dict, sections: dict, proxies: dict = None, ):
        self.signes = signes
        self.sections = sections
        self.proxies = proxies

    def get_sign(self, signe: dict):
        response = requests.get(signe["url"], proxies=self.proxies, verify=False)
        tree = html.fromstring(response.content)

        text = f"### {signe['icon']} {signe['name']}"
        if len(signe['users']) > 0:
            text = f"{text} : {', '.join(signe['users'])}"
        text = f"{text}\n"

        for section in self.sections:
            topic = tree.xpath(f'//div[@class="c-horoscope-topic-card"][contains(div/h3/text(), "{section["name"]}")]/p')
            if len(topic) > 0:
                topic_content = topic[0].text
                text = f"{text}\n###### {section['icon']} {section['name']}\n{topic_content}\n"
        return text

    def collect(self) -> typing.Generator:
        for signe in self.signes:
            if len(signe['users']) > 0:
                yield self.get_sign(signe)

if __name__ == "__main__":
    with open("config.json", "r") as f:
        config = json.load(f)

    for s in Horoscopper(proxies=config["proxies"], **config["horoscope"]).collect():
        print(s)
        print("---")
