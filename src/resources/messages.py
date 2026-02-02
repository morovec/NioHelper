import json
from dataclasses import dataclass

@dataclass
class Messages:
    tg_startup: str
    tg_shutdown: str

with open("src/resources/msg_data.json", "r", encoding="utf-8") as file:
    raw_data = json.load(file)

messages = Messages(**raw_data)