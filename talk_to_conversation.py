import os
import json
import time
from pathlib import Path
from rich import print

def now():
    """datetime now"""
    return time.strftime("%Y%m%d%H%M%S")

def write_json(filename, data):
    """write to json file"""
    with open(filename, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, sort_keys=True, indent=4, ensure_ascii=False)
    return True

def save_conversation(messages):
    if len(messages) < 2:
        # we skip system message
        return
    directory = Path('conversations')
    directory.mkdir(exist_ok=True)
    filename = f"{now()}.json"
    path = directory / filename
    write_json(path, messages)
    print(f"[*] conversation saved to: [cyan]{path}[/cyan]")

# load conversation from .txt
filename = 'conversations/20231201-talk.txt'
system_message = {"role": "system", "content": "rule: reply directly without long summaries and comments, in few words"}
messages = [system_message]
matching = {
    'me': 'user',
    'gpt': 'assistant',    
}
path = Path(filename)
lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
for line in lines:
    _, role, content = line.split(None, maxsplit=2)
    role = role.rstrip(':')
    role = matching[role]
    submessage = {'role': role, 'content': content}
    messages.append(submessage)

# save conversation as .json
save_conversation(messages)
