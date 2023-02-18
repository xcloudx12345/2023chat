# Import the necessary libraries
import os
import discord
from revChatGPT.V1 import Chatbot
from revChatGPT.V1 import Error
from EdgeGPT import Chatbot as Ebot
import json

# Get config data as dictionary
CONFIG_FILE_PATH = os.path.abspath(__file__ + "/../../config.json")

def get_config() -> dict:
    with open(CONFIG_FILE_PATH, 'r') as f:
        return json.load(f)

def save_config(config: dict):
    with open(CONFIG_FILE_PATH, 'w') as f:
        json.dump(config, f)

# Call the get_config function to retrieve config data as a dict
#bot = Ebot(cookiePath="")
chatbot = Chatbot(config={
  "email": os.environ['email'],
  "password": os.environ['password']
})
# handle_response function returns response from chatbot to a message
async def handle_response(message) -> str:
    config = get_config()
    conversation_id = config.get("conversation_id")
    
    if conversation_id == "":
        # Conversation ID and parent ID not set in config, make a new API call to the chatbot
        response = []
        conversation_id=""
        #parent_id=""
        try:
            for data in chatbot.ask(message):
                response = data["message"][len("") :]
                conversation_id = data["conversation_id"]
                #parent_id = data["parent_id"]
            responseMessage = "".join(response)
            config["conversation_id"] = conversation_id
            #config["parent_id"] = parent_id
            save_config(config)
            return responseMessage
        except discord.errors.HTTPException:
            return Error()
    else:
        # Conversation ID and parent ID are set in config, add them to the API call to continue the conversation
        response = []
        for data in chatbot.ask(message, conversation_id=conversation_id):
            response = data["message"][len("") :]
        responseMessage = "".join(response)
        return responseMessage

async def EDGE_response(message) -> str:
    bot = Ebot()
    response = await bot.ask(prompt=message)
    responseMessage = response["item"]["messages"][1]["adaptiveCards"][0]["body"][0]["text"]
    return responseMessage
    
    '''response = []
    for data in chatbot.ask(message,conversation_id="DAN",parent_id="DAN"):
        response = data["message"][len("") :]
    responseMessage = "".join(response)
    # Return response as string
    return responseMessage'''
    
async def get_input(prompt):
    """
    Multi-line input function
    """
    # Display the prompt
    print(prompt, end="")

    # Initialize an empty list to store the input lines
    lines = []

    # Read lines of input until the user enters an empty line
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)

    # Join the lines, separated by newlines, and store the result
    user_input = "\n".join(lines)

    # Return the input
    return user_input