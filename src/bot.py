import os
import discord
from discord import app_commands
from discord.ext import commands
from revChatGPT.V1 import Chatbot
from revChatGPT.V1 import Error
from src import responses
from src import log
import json
import asyncio

logger = log.setup_logger(__name__)
config = responses.get_config()
isPrivate = False
tiengviet = "từ giờ luôn trả lời tôi bằng tiếng việt"
# Get config data as dictionary
CONFIG_FILE_PATH = os.path.abspath(__file__ + "/../../config.json")
long_text = 0
def get_config() -> dict:
    with open(CONFIG_FILE_PATH, 'r') as f:
        return json.load(f)
def save_config(config: dict):
    with open(CONFIG_FILE_PATH, 'w') as f:
        json.dump(config, f)

# Call the get_config function to retrieve config data as a dict
chatbot = Chatbot(config={
    "email": os.environ['email'],
    "password": os.environ['password']
})

class aclient(discord.Client):

    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.playing,
                                         name="/chat | /help")


async def send_message(message, user_message):
    await message.response.defer(ephemeral=isPrivate)
    try:
        response = '> **' + user_message + '** - <@' + \
            str(message.user.id) + '> \n\n'
        response = f"{response}{await responses.handle_response(user_message)}"
        if len(response) > 1900:
            # Split the response into smaller chunks of no more than 1900 characters each(Discord limit is 2000 per chunk)
            if "```" in response:
                # Split the response if the code block exists
                parts = response.split("```")
                # Send the first message
                await message.followup.send(parts[0])
                # Send the code block in a seperate message
                code_block = parts[1].split("\n")
                formatted_code_block = ""
                for line in code_block:
                    while len(line) > 1900:
                        # Split the line at the 50th character
                        formatted_code_block += line[:1900] + "\n"
                        line = line[1900:]
                    formatted_code_block += line + "\n"  # Add the line and seperate with new line

                # Send the code block in a separate message
                if len(formatted_code_block) > 2000:
                    code_block_chunks = [
                        formatted_code_block[i:i + 1900]
                        for i in range(0, len(formatted_code_block), 1900)
                    ]
                    for chunk in code_block_chunks:
                        await message.followup.send("```" + chunk + "```")
                else:
                    await message.followup.send("```" + formatted_code_block +
                                                "```")

                # Send the remaining of the response in another message

                if len(parts) >= 3:
                    await message.followup.send(parts[2])
            else:
                response_chunks = [
                    response[i:i + 1900]
                    for i in range(0, len(response), 1900)
                ]
                for chunk in response_chunks:
                    await message.followup.send(chunk)
        else:
            await message.followup.send(response)
    except Exception as e:
        await message.followup.send(
            "> **Error: Lỗi rồi, vui lòng thử lại sau!**")
        logger.exception(f"Error while sending message: {e}")


async def send_message_new(message, user_message):
    await message.response.defer(ephemeral=isPrivate)
    try:
        config = get_config()
        conversation_id = config.get("conversation_id")
        response0 = '> **' + user_message + '** - <@' + \
            str(message.user.id) + '> \n\n'
        if len(response0) <= 1900:
            await message.edit_original_response(content=response0)
        else:
            await message.edit_original_response(content="Nội dung tin nhắn dài hơn 1900 ký tự, vui lòng nhập tin nhắn ngắn hơn!")
        if conversation_id == "":
            # Conversation ID not set in config, make a new API call to the chatbot
            response = []
            try:
                
                for data in chatbot.ask(user_message):
                    response = data["message"][len(""):]
                    conversation_id = data["conversation_id"]
                    response = [response0, response]
                    responseMessage = "".join(response)
                    await send_long_message(message, responseMessage)
                config["conversation_id"] = conversation_id
                save_config(config)
                return  # await send_long_message(message, responseMessage)
            except discord.errors.HTTPException:
                print(Error)
                await message.followup.send(
                    "> **Error: Lỗi rồi, vui lòng thử lại sau!**")
        else:
            response = []
            channel_id=message.channel_id
            message_id=message.message.id
            # Conversation ID is set in config, add it to the API call to continue the conversation
            for data in chatbot.ask(user_message,conversation_id=conversation_id):
                response = data["message"][len(""):]
                #response = [response0, response]
                responseMessage = "".join(response)
                if response == []:
                    await message.followup.send("\n Trả lời:")
                else:
                    await asyncio.gather(send_long_message(message, message_id, channel_id, responseMessage))
            return  # await send_long_message(message, responseMessage)
    except Exception as e:
        await message.followup.send(
            "> **Error: Lỗi rồi, vui lòng thử lại sau!**")
        logger.exception(f"Error while sending message: {e}")

async def send_long_message(interaction, message_id, channel_id, response1):
    bot = commands.Bot()
    channel = bot.get_channel(channel_id)
    msg = message = await interaction.channel.fetch_message(message_id)
    
    if len(msg.content) > 1900:
        new_message = await channel.send(content=response1)
        send_long_message(new_message.id)
    else:
        #new_text = old_messages[0].content+response1
        await msg.edit(content=response1)

async def send_start_prompt(client):
    import os.path

    config_dir = os.path.abspath(__file__ + "/../../")
    prompt_name = 'starting-prompt.txt'
    prompt_path = os.path.join(config_dir, prompt_name)
    try:
        if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
            with open(prompt_path, "r", encoding='utf-8') as f:
                prompt = f.read()
                if config['discord_channel_id']:
                    logger.info("Send starting prompt with size %s",
                                len(prompt))
                    responseMessage = await send_long_message(prompt)
                    channel = client.get_channel(
                        int(config['discord_channel_id']))
                    await channel.send(responseMessage)
                    logger.info("Starting prompt response: %s",
                                responseMessage)
                else:
                    logger.info(
                        "No Channel selected. Skip sending starting prompt.")
        else:
            logger.info("No %s. Skip sending starting prompt.", prompt_name)
    except Exception as e:
        logger.exception("Error while sending starting prompt: %s", e)


def run_discord_bot():
    client = aclient()
    @client.event
    async def on_ready():
        await send_start_prompt(client)
        await client.tree.sync()
        logger.info('%s is now running!', client.user)
        #await responses.handle_response(tiengviet)
        #await responses.DAN_response(DANcreate)

    @client.event
    async def on_message(message):
        if message.author == client.user or message.author.bot:
            return
        with open('db.json', 'r') as file:
            data = json.load(file)
        if message.guild is None:
            await message.channel.send(
                "Xin lỗi, tôi không trả lời tin nhắn riêng.")
            return
        # your code to handle messages in servers here
        if data.get(str(message.guild.id)) is None:
            return
        if str(message.channel.id) in data[str(message.guild.id)]:
            logger.info("\x1b[31m%s#%s\x1b[0m : '%s' (%s)",
                        message.author.name, message.author.discriminator,
                        message.content, message.channel.name)
        try:
            async with message.channel.typing():
                #multi_line = await responses.get_input(message.content)
                response = await responses.EDGE_response(message.content)
                if len(response) > 2000:
                    # Split the response into smaller chunks of no more than 1900 characters each (Discord limit is 2000 per chunk)
                    if "```" in response:
                        # Split the response if the code block exists
                        parts = response.split("```")
                        # Send the first message
                        await message.channel.send(
                            f"> **{message.content}** - <@{message.author.id}>"
                        )
                        await message.channel.send(parts[0])
                        # Send the code block in a separate message
                        code_block = parts[1].split("\n")
                        formatted_code_block = ""
                        for line in code_block:
                            while len(line) > 1900:
                                # Split the line at the 50th character
                                formatted_code_block += line[:1900] + "\n"
                                line = line[1900:]
                            formatted_code_block += line + "\n"  # Add the line and separate with a new line
                        # Send the code block in a separate message
                        if len(formatted_code_block) > 2000:
                            code_block_chunks = [
                                formatted_code_block[i:i + 1900] for i in
                                range(0, len(formatted_code_block), 1900)
                            ]
                            for chunk in code_block_chunks:
                                await message.channel.send("```" + chunk +
                                                           "```")
                        else:
                            await message.channel.send("```" +
                                                       formatted_code_block +
                                                       "```")
                        # Send the remaining of the response in another message
                        if len(parts) >= 3:
                            await message.channel.send(parts[2])
                    else:
                        response_chunks = [
                            response[i:i + 1900]
                            for i in range(0, len(response), 1900)
                        ]
                        for chunk in response_chunks:
                            await message.channel.send(chunk)
                else:
                    await message.channel.send(
                        f"> **{message.content}** - <@{message.author.id}>\n\n{response}"
                    )
        except Exception as e:
            await message.channel.send(
                "> **Error: Lỗi rồi, vui lòng thử lại sau!**")
            logger.exception(f"Error while sending message: {e}")

    @client.tree.command(name="chat", description="Chat với con bot")
    async def chat(interaction: discord.Interaction, *, message: str):

        if interaction.guild is None:
            await interaction.user.send(
                "Xin lỗi, tôi không trả lời tin nhắn riêng.")
            return
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        user_message = message
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
        async with interaction.user.typing():
            try:
                await send_message_new(interaction, user_message)
            except Exception as error:
                print(error)

    @client.tree.command(name="private",description="Chuyển sang chế độ riêng tư")
    async def private(interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.user.send(
                "Xin lỗi, tôi không trả lời tin nhắn riêng.")
            return
        global isPrivate
        await interaction.response.defer(ephemeral=False)
        if not isPrivate:
            isPrivate = not isPrivate
            logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
            await interaction.followup.send(
                "> **Info: Từ giờ, bot sẽ trả lời bạn ở chế độ riêng tư, chỉ có bạn mới xem được câu trả lời. Để chuyển lại chế độ public, gõ `/public`**"
            )
        else:
            logger.info("You already on private mode!")
            await interaction.followup.send(
                "> **Warn: Bạn đang ở chế độ riêng tư rồi. Để chuyển lại chế độ public, gõ `/public`**"
            )

    @client.tree.command(name="public",description="Chuyển sang chế độ công khai")
    async def public(interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.user.send(
                "Xin lỗi, tôi không trả lời tin nhắn riêng.")
            return
        global isPrivate
        await interaction.response.defer(ephemeral=False)
        if isPrivate:
            isPrivate = not isPrivate
            await interaction.followup.send(
                "> **Info: Từ giờ, mọi người sẽ thấy nội dung bot trả lời bạn. Để chuyển lại chế độ private, gõ `/private`**"
            )
            logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
        else:
            await interaction.followup.send(
                "> **Warn: Bạn đang ở chế độ public rồi. Để chuyển lại chế độ private, gõ `/private`**"
            )
            logger.info("You already on public mode!")

    @client.tree.command(name="reset", description="Xóa ký ức bot")
    async def reset(interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.user.send(
                "Xin lỗi, tôi không trả lời tin nhắn riêng.")
            return
        chatbot.delete_conversation(config['conversation_id'])
        config['conversation_id'] = ""
        save_config(config)
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(
            "> **Info: Ây da mất trí nhớ gòi, tui là đâu, đây là ai!.**")
        logger.warning(
            "\x1b[31mChatGPT bot has been successfully reset\x1b[0m")
        await send_start_prompt(client)

    @client.tree.command(name="auto",description="Lưu id kênh và tên kênh để bot trả lời tự động")
    async def auto(interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.user.send(
                "Xin lỗi, tôi không trả lời tin nhắn riêng.")
            return
        channel_id = str(interaction.channel_id)
        channel_name = str(interaction.channel)
        guild_id = str(interaction.guild.id)
        guild_name = str(interaction.guild)
        await interaction.response.defer(ephemeral=False)
        try:
            with open('db.json', 'r') as f:
                channels = json.load(f)
        except FileNotFoundError:
            channels = {}

        if guild_id not in channels:
            channels[guild_id] = {}

        if channel_id in channels[guild_id]:
            del channels[guild_id][channel_id]
            with open('db.json', 'w') as f:
                json.dump(channels, f)
            await interaction.followup.send(
                f"Kênh `{channel_name}` đã xóa khỏi list trả lời tự động của máy chủ `{guild_name}`."
            )
        else:
            channels[guild_id][channel_id] = channel_name
            with open('db.json', 'w') as f:
                json.dump(channels, f)
            await interaction.followup.send(
                f"Kênh `{channel_name}` đã thêm vào list trả lời tự động của máy chủ `{guild_name}`."
            )

    @client.tree.command(name="help", description="Trợ giúp")
    async def help(interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.user.send(
                "Xin lỗi, tôi không trả lời tin nhắn riêng.")
            return
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(
            ":star:**LỆNH CƠ BẢN** \n    `/chat [message]` Chat với bot!\n    `/public` Chuyển sang chế độ Public\n    `/private` Chuyển sang chế độ Private\n    `/auto` Lưu kênh chat để bot trả lời tự động\n    `/reset` Xóa ký ức bot"
        )
        logger.info("\x1b[31mSomeone need help!\x1b[0m")

    #TOKEN = os.getenv("discord_bot_token")
    TOKEN = os.environ['discord_bot_token']
    client.run(TOKEN)
