# Import the necessary libraries
import os
from EdgeGPT import Chatbot
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

# Initialize the AsyncChatbot class with API key from either config or environment variable
#chatbot = AsyncChatbot(api_key=os.environ['openAI_key'])

# handle_response function returns response from chatbot to a message
async def handle_response(message) -> str:
    bot = Chatbot()
    # Get response from chatbot
    response = await bot.ask(prompt=message)
    await bot.close()
    # Select the first choice from response
    responseMessage = response["choices"][0]["text"]

    # Return response as string
    return responseMessage
