import argparse
import os
import re
import sys
import time
from pathlib import Path
from string import ascii_letters, digits

import requests
from dotenv import dotenv_values
from openai import BadRequestError, OpenAI
from rich import print
from rich.prompt import Prompt
from unidecode import unidecode


def save_img_from_url(url, path):
    """save image from specified url, to specified local path"""
    response = requests.get(url)
    if response.status_code != 200:
        return False
    with open(path, 'wb') as f:
        f.write(response.content)
    return True


def sanitize_name(name):
    """sanitize file name by removing non ascii characters, and filling substrings with dashes
    it doesnt include suffix, so pass name only
    https://stackoverflow.com/questions/3878555/how-to-replace-repeated-instances-of-a-character-with-a-single-instance-of-that
    """
    allowed_chars = ascii_letters + digits
    new_name = unidecode(name)
    new_name_chars = [c if c in allowed_chars else "-" for c in new_name]
    new_name = "".join(new_name_chars).strip("-")
    new_name = re.sub("\-\-+", "-", new_name)
    new_name = new_name[:200].rstrip('-')
    return new_name


if __name__ == "__main__":
    os.chdir(str(Path(__file__).parent))

    # **** load config ****
    config = dotenv_values()
    OPENAI_API_KEY = config["OPENAI-API-KEY"]
    client = OpenAI(api_key=OPENAI_API_KEY)

    # **** args ****
    parser = argparse.ArgumentParser()
    parser.add_argument("prompt", help="Text prompt to generate image")
    parser.add_argument("-o", "--output", required=False, help="Prefix for generated image(s) name")
    parser.add_argument("-n", "--number", required=False, default=1, type=int, help="Number of images to generate")
    parser.add_argument("--skip", required=False, action='store_true', help="If error occur skip and go next")
    parser.add_argument("--style", default="vivid", choices=["vivid", "natural"])
    args = parser.parse_args()
    PROMPT = args.prompt
    NUMBER = args.number
    if NUMBER > 10:
        response = Prompt.ask('[yellow bold][>] do you really want to generate more than 10 images? (yes/No)[/yellow bold]')
        if not response.lower() in ('yes', 'y'):
            sys.exit()
    if args.output:
        name_prefix = sanitize_name(args.output)
    else:
        name_prefix = sanitize_name(PROMPT)
    SKIP = args.skip
    if args.style:
        STYLE = args.style
    else:
        # https://taurit.pl/dalle-3-style-vivid-vs-natural/
        # vivid causes the model to lean towards generating hyper-real and dramatic images
        # natural causes the model to produce more natural, less hyper-real looking images
        STYLE = 'vivid'

    # **** query setup ****
    # https://openai.com/api/pricing/
    # DALL·E 3 Standard 1024×1024 $0.040 / image
    model = "dall-e-3"
    size = "1024x1024"
    quality = "standard"
    print(f'[*] query setup: {model=} {size=} {quality=}')
    print(f'[*] prompt: [cyan bold]{PROMPT}[/cyan bold]')
    print(f'[*] it will cost you: {NUMBER} * {0.040}$ => {NUMBER * 0.040}$')

    # **** iterate ****
    padding = len(str(NUMBER))
    directory = Path('dalle')
    directory.mkdir(exist_ok=True)
    for index in range(1, NUMBER+1):
        print(f'{index}/{NUMBER})')
        try:
            # **** query for image ****
            response = client.images.generate(
                model=model,
                prompt=PROMPT,
                size=size,
                style=STYLE,
                quality=quality,
                n=1,  # You must provide n=1 for this model
            )
            url = response.data[0].url
        except BadRequestError as err:
            print(f'[red]{err}[/red]')
            if SKIP:
                continue
            else:
                break
        except KeyboardInterrupt:
            print(f'\n[yellow bold][*] broken by user[/yellow bold]')
            break

        # **** save images to disk ****
        now = time.strftime('%H%M%S')
        filename = f'{name_prefix}-{now}-{index:0{padding}}.png'
        filepath = directory.joinpath(filename)
        save_img_from_url(url, filepath)
        print(f'[*] image saved to: [magenta bold]{filepath}[/magenta bold]')
