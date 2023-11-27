import os
import sys
from collections import namedtuple
from pathlib import Path

from dotenv import dotenv_values
from openai import OpenAI
from rich import print
from rich.columns import Columns
from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax

Block = namedtuple("Block", ["content", "type"])


def script_path():
    """set current path, to script path"""
    current_path = str(Path(__file__).parent)
    os.chdir(current_path)
    return current_path


def ask_chat(messages):
    response = client.chat.completions.create(
            model=model,
            n=1,
            temperature=0.5,
            messages=messages,
        )
    message = response.choices[0].message.model_dump()
    del message['function_call']
    del message['tool_calls']
    return message


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
    known_languages = {"python", "javascript", "html"}
    if block.type in known_languages:
        language = block.type
    else:
        language = None
    highlight_code(block.content, language, codebox=True)


def highlight_code(content, language, codebox=False):
    highlighted = Syntax(content, language, theme='monokai', line_numbers=False, indent_guides=False, word_wrap=True)
    highlighted = Columns([Panel(highlighted)])
    print(highlighted)


def usage():
    print("Usage")
    print("    cls, clear       -clear terminal")
    print("    exit, quit       -clear terminal")
    print("    context          -switch context flag")
    print("    model            -show current model")
    print("    models           -list all models")
    print("    talk             -show talk messages")
    print("    help             -this usage")


if __name__ == "__main__":
    script_path()
    os.system('color')
    
    # load config
    # create .env file with OPENAI-API-KEY field
    config = dotenv_values()
    client = OpenAI(api_key=config["OPENAI-API-KEY"])

    # talk to gpt
    model = "gpt-3.5-turbo"
    context = True  # keep conversation context
    system_message = {"role": "system", "content": "rule: reply directly without long summaries and comments, in few words"}
    messages = [system_message]
    while True:
        try:
            question = Prompt.ask("[cyan][*] me[/cyan]")
        except KeyboardInterrupt:
            print()
            continue
        question = question.strip()
        if not question:
            continue
        if question in ('cls', 'clear'):
            os.system('cls')
            continue
        elif question in ('exit', 'quit'):
            print()
            break
        elif question == "context":
            context = not context
            print(f"[*] keep context set to: {context}")
            if not context:
                # TODO: think of storing last conversation in json
                messages = [system_message]
            continue
        elif question == "talk":
            print(messages)
            continue
        elif question == "help":
            usage()
            continue
        elif question == 'model':
            print(f'[*] debug: [magenta]{model}[magenta]')
            continue
        elif question == 'models':
            models = client.models.list()
            print(models)
            continue

        # prepare messages
        user_message = {"role": "user", "content": question}
        if context:
            messages.append(user_message)
        else:
            messages = [system_message, user_message]

        # ask & show answer
        gpt_message = ask_chat(messages)
        if context:
            messages.append(gpt_message)
        answer = gpt_message['content']
        blocks = split_codeblocks(answer)
        if (len(blocks) == 1) and blocks[0].type == 'text':
            print(f'[*] gpt: [yellow]{answer}[/yellow]')
        else:
            print(f'[*] gpt:')
            for block in blocks:
                show_block(block)
