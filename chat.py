import json
import os
import time
from collections import namedtuple
from pathlib import Path

try:
    import ollama
except ModuleNotFoundError as err:
    # print(err)
    # print('you have to install ollama (`pip install ollama`), as well as model that you specify')
    pass
from dotenv import dotenv_values
from openai import OpenAI
from rich import print
from rich.columns import Columns
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax

Block = namedtuple("Block", ["content", "type"])


class OllamaClient:
    def __init__(self, model, system_message=None, context=True):
        self.model = model
        self.system_message = system_message
        self.messages = [self.system_message]
        self.context = context
        self.conversation_id = self.__now()

    def ask(self, content):
        message = {"role": "user", "content": content}
        self.messages.append(message)
        response = ollama.chat(model=self.model, messages=self.messages)
        reply = response['message']
        if self.context:
            # keep conversation
            self.messages.append(reply)
        answer = reply['content']
        return answer

    def get_models(self):
        """show information about locally available models"""
        print(ollama.list())

    def get_model(self):
        """show information about currently used model"""
        print(f'[*] current model: {self.model}')

    def switch_context(self):
        self.context = not self.context
        if not self.context:
            self.save_conversation()
            self.messages = [self.system_message]
        print(f'[*] context set to: {self.context}')

    def __now(self):
        """datetime now"""
        return time.strftime("%Y%m%d%H%M%S")

    def save_conversation(self):
        if len(self.messages) < 2:
            # we skip system message
            return
        directory = Path('conversations')
        directory.mkdir(exist_ok=True)
        filename = f'{self.conversation_id}-{self.model}.json'
        path = directory / filename
        write_json(path, self.messages)
        print(f"[*] conversation saved to: [cyan]{path}[/cyan]")
        self.conversation_id = self.__now()

    def load_conversation(self):
        self.save_conversation()  # save current conversation
        conversations_directory = Path('conversations')
        conversations_list = [item for item in conversations_directory.iterdir() if item.suffix == '.json']
        conversations_match = {str(index):item for index, item in enumerate(conversations_list, start=1)}
        conversations_str = '\n'.join([f'    {key}) [cyan]{path}[/cyan]' for (key, path) in conversations_match.items()])
        choose_list = f'[*] choose from list:\n{conversations_str}'
        print(choose_list)
        try:
            load_input = input()
        except KeyboardInterrupt:
            print()
            return False
        path_to_load = conversations_match.get(load_input, False)
        if not path_to_load:
            print(f'[red]\[x] wrong choice')
            return False
        loaded_messages = read_json(path_to_load)
        if not loaded_messages:
            print(f'[red]\[x] failed to load conversation from: {load_input}')
        else:
            self.messages = loaded_messages
            self.conversation_id = path_to_load.stem.split('-', maxsplit=1)[0]
            print(f'[green][*] conversation loaded')

    def usage(self):
        print("Usage")
        print("    cls, clear       -clear terminal")
        print("    exit, quit       -clear terminal")
        print("    context          -switch context flag")
        print("    model            -show current model")
        print("    models           -list all models")
        print("    id               -conversation ID")
        print("    load             -load conversation")
        print("    talk             -show talk messages")
        print("    help             -this usage")


class GPTClient:
    def __init__(self, model, system_message=None, context=True):
        self.model = model  # gpt-4, gpt-3.5-turbo
        config = dotenv_values()
        self.client = OpenAI(api_key=config["OPENAI-API-KEY"])
        self.system_message = system_message
        self.messages = [self.system_message]
        self.context = context
        self.conversation_id = self.__now()

    def ask(self, content):
        message = {"role": "user", "content": content}
        self.messages.append(message)
        response = self.client.chat.completions.create(
                model=self.model,
                n=1,
                temperature=0.5,
                messages=self.messages,
        )
        reply = response.choices[0].message.model_dump()
        del reply['function_call']
        del reply['tool_calls']
        del reply['refusal']
        if self.context:
            # keep conversation
            self.messages.append(reply)
        answer = reply['content']
        return answer

    def get_models(self):
        """show information about locally available models"""
        models = self.client.models.list()
        print(models)

    def get_model(self):
        """show information about currently used model"""
        print(f'[*] current model: {self.model}')

    def switch_context(self):
        self.context = not self.context
        if not self.context:
            self.save_conversation()
            self.messages = [self.system_message]
        print(f'[*] context set to: {self.context}')

    def __now(self):
        """datetime now"""
        return time.strftime("%Y%m%d%H%M%S")

    def save_conversation(self):
        if len(self.messages) < 2:
            # we skip system message
            return
        directory = Path('conversations')
        directory.mkdir(exist_ok=True)
        filename = f'{self.conversation_id}-{self.model}.json'
        path = directory / filename
        write_json(path, self.messages)
        print(f"[*] conversation saved to: [cyan]{path}[/cyan]")
        self.conversation_id = self.__now()

    def load_conversation(self):
        self.save_conversation()  # save current conversation
        conversations_directory = Path('conversations')
        conversations_list = [item for item in conversations_directory.iterdir() if item.suffix == '.json']
        conversations_match = {str(index):item for index, item in enumerate(conversations_list, start=1)}
        conversations_str = '\n'.join([f'    {key}) [cyan]{path}[/cyan]' for (key, path) in conversations_match.items()])
        choose_list = f'[*] choose from list:\n{conversations_str}'
        print(choose_list)
        try:
            load_input = input()
        except KeyboardInterrupt:
            print()
            return False
        path_to_load = conversations_match.get(load_input, False)
        if not path_to_load:
            print(f'[red]\[x] wrong choice')
            return False
        loaded_messages = read_json(path_to_load)
        if not loaded_messages:
            print(f'[red]\[x] failed to load conversation from: {load_input}')
        else:
            self.messages = loaded_messages
            self.conversation_id = path_to_load.stem.split('-', maxsplit=1)[0]
            print(f'[green][*] conversation loaded')

    def usage(self):
        print("Usage")
        print("    cls, clear       -clear terminal")
        print("    exit, quit       -clear terminal")
        print("    context          -switch context flag")
        print("    model            -show current model")
        print("    models           -list all models")
        print("    id               -conversation ID")
        print("    load             -load conversation")
        print("    talk             -show talk messages")
        print("    help             -this usage")


def write_json(filename, data):
    """write to json file"""
    with open(filename, 'w', encoding='utf-8') as fp:
        json.dump(data, fp, sort_keys=True, indent=4, ensure_ascii=False)
    return True


def read_json(filename):
    """read json file to dict"""
    data = {}
    try:
        with open(filename, encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print('[x] FileNotFoundError: {}'.format(filename))
    return data


def split_codeblocks(text):
    """Extracts the code block section from a markdown text."""
    lines = iter(text.splitlines())
    blocks = []
    rows = []
    skip = False
    while True:
        if not skip:
            line = next(lines, None)
            if line is None:
                break
        if line.startswith("```"):
            skip = False
            block_type = line.removeprefix("```").strip()
            while True:
                line = next(lines, None)
                if (line is None) or (line.startswith("```")):
                    if rows:
                        block = Block(content="\n".join(rows), type=block_type)
                        blocks.append(block)
                        rows = []
                    break
                else:
                    rows.append(line)
        else:
            block_type = 'text'
            rows.append(line)
            while True:
                line = next(lines, None)
                if (line is not None) and line.startswith("```"):
                    # to change state, to go code section
                    skip = True
                if (line is None) or (line.startswith("```")):
                    if rows:
                        block = Block(content="\n".join(rows), type=block_type)
                        blocks.append(block)
                        rows = []
                    break
                else:
                    rows.append(line)
    return blocks


def show_block(block):
    """Highlights a code block using the rich library."""
    if block.type == "text":
        print(f'[yellow]{block.content}[/yellow]')
        return
    known_languages = {
        "bash",
        "cpp",
        "css",
        "dart",
        "go",
        "groovy",
        "haskell",
        "html",
        "java",
        "javascript",
        "json",
        "julia",
        "kotlin",
        "lua",
        "markdown",
        "matlab",
        "perl",
        "php",
        "powershell",
        "python",
        "r",
        "ruby",
        "rust",
        "scala",
        "sql",
        "swift",
        "typescript",
        "xml",
        "yaml"
    }
    if block.type in known_languages:
        language = block.type
    else:
        language = None
    highlight_code(block.content, language, codebox=True)


def highlight_code(content, language, codebox=False):
    highlighted = Syntax(
        content,
        language,
        theme='monokai',
        line_numbers=False,
        indent_guides=False,
        word_wrap=True
    )
    highlighted = Columns([Panel(highlighted)])
    print(highlighted)


def pretty_print_answer(answer):
    """split into codeblocks and highlight"""
    blocks = split_codeblocks(answer)
    if (len(blocks) == 1) and blocks[0].type == 'text':
        print(f'[*] gpt: [yellow]{answer}[/yellow]')
    else:
        print(f'[*] gpt:')
        for block in blocks:
            show_block(block)


def clear():
    """clear terminal"""
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')


if __name__ == "__main__":
    os.chdir(str(Path(__file__).parent))
    if os.name == 'nt':
        os.system('color')

    # **** create chat client ****
    system_message = {
        "role": "system",
        "content": "rule: reply directly without long summaries and comments, in few words"
    }
    # client = OllamaClient(model="codellama", system_message=system_message, context=True)
    client = GPTClient(model="gpt-4", system_message=system_message, context=True)

    # **** ollama chat ****
    while True:
        try:
            question = Prompt.ask("[cyan][*] you[/cyan]")
        except KeyboardInterrupt:
            print()
            continue

        question = question.strip()
        if not question:
            continue

        if question in ('cls', 'clear'):
            clear()
            continue

        elif question in ('exit', 'quit'):
            print()
            break

        elif question == "context":
            client.switch_context()
            continue

        elif question == "talk":
            print(client.messages)
            continue

        elif question == "id":
            print(f'[*] conversation ID: [cyan]{client.conversation_id}[/cyan]')
            continue

        elif question == "help":
            client.usage()
            continue

        elif question == 'models':
            client.get_models()
            continue

        elif question == 'model':
            client.get_model()
            continue

        elif question == 'load':
            client.load_conversation()
            continue

        # **** ask chat ****
        answer = client.ask(question)
        pretty_print_answer(answer)

    # **** save last conversation ****
    client.save_conversation()
