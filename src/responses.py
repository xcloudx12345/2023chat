# Import the necessary libraries
import os
from revChatGPT.V1 import Chatbot
import json

# Get config data as dictionary
def get_config() -> dict:
    # Get the path for the config.json file using ospath library
    config_dir = os.path.abspath(__file__ + "/../../")
    config_name = 'config.json'
    config_path = os.path.join(config_dir, config_name)

    # Load the config.json file as a dictionary
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Return config dict 
    return config

# Call the get_config function to retrieve config data as a dict
config = get_config()
chatbot = Chatbot(os.environ['email'],os.environ['password'])

# handle_response function returns response from chatbot to a message
async def handle_response(message) -> str:
    for data in chatbot.ask(prompt, conversation_id=chatbot.config.get("conversation"), parent_id=chatbot.config.get("parent_id")
        response = data["message"]
        #responseMessage = "".join(response)
        return response
    # Return response as string
    
async def DAN_response(message) -> str:
    response = []
    async for line in chatbot.ask(message,"DAN"):
        response.append(line["choices"][0]["text"].replace("<|im_end|>", ""))
        responseMessage = "".join(response)
    # Return response as string
        return responseMessage
