import base64
import sys
from pathlib import Path
from dotenv import dotenv_values
from openai import OpenAI

def encode_image(image_path):
    """Function to encode the image"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# **** config ****
config = dotenv_values()
OPENAI_API_KEY = config["OPENAI-API-KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

# **** read & encode image content ****
args = sys.argv[1:]
if not args:
    print("usage:\n    python ocr.py image.png")
    sys.exit()
image_path = args[0]
if not Path(image_path).exists():
    raise Exception(f'no such file: {image_path}')
base64_image = encode_image(image_path)

# **** ask gpt ****
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "get text from image. Return it and nothing more",
            },
            {
            "type": "image_url",
            "image_url": {"url":  f"data:image/jpeg;base64,{base64_image}"},
            },
        ],
        }
    ],
)
answer = response.choices[0]
content = answer.message.content
print(content)
