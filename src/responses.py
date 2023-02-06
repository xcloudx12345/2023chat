import os
from revChatGPT.Official import AsyncChatbot
import json
from asgiref.sync import sync_to_async


def get_config() -> dict:
    # get config.json path
    config_dir = os.path.abspath(__file__ + "/../../")
    config_name = 'config.json'
    config_path = os.path.join(config_dir, config_name)

    with open(config_path, 'r') as f:
        config = json.load(f)

    return config


config = get_config()
#chatbot = Chatbot(api_key=config['openAI_key'])
chatbot = AsyncChatbot(api_key=os.environ['openAI_key'])

async def handle_response(message) -> str:
    response = await chatbot.ask(message)
    responseMessage = response["choices"][0]["text"]

    return responseMessage
