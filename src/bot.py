import os
import discord
from discord import app_commands
from src import responses
from src import log
import json

logger = log.setup_logger(__name__)

config = responses.get_config()

isPrivate = False


class aclient(discord.Client):
    def __init__(self) -> None:
        super().__init__(intents=discord.Intents.all())
        self.tree = app_commands.CommandTree(self)
        self.activity = discord.Activity(type=discord.ActivityType.watching, name="/chat | /help")


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
                    code_block_chunks = [formatted_code_block[i:i+1900]
                                         for i in range(0, len(formatted_code_block), 1900)]
                    for chunk in code_block_chunks:
                        await message.followup.send("```" + chunk + "```")
                else:
                    await message.followup.send("```" + formatted_code_block + "```")

                # Send the remaining of the response in another message

                if len(parts) >= 3:
                    await message.followup.send(parts[2])
            else:
                response_chunks = [response[i:i+1900]
                                   for i in range(0, len(response), 1900)]
                for chunk in response_chunks:
                    await message.followup.send(chunk)
        else:
            await message.followup.send(response)
    except Exception as e:
        await message.followup.send("> **Error: Lỗi rồi, vui lòng thử lại sau!**")
        logger.exception(f"Error while sending message: {e}")


async def send_start_prompt(client):
    import os.path

    config_dir = os.path.abspath(__file__ + "/../../")
    prompt_name = 'starting-prompt.txt'
    prompt_path = os.path.join(config_dir, prompt_name)
    try:
        if os.path.isfile(prompt_path) and os.path.getsize(prompt_path) > 0:
            with open(prompt_path, "r",encoding='utf-8') as f:
                prompt = f.read()
                if config['discord_channel_id']:
                    logger.info("Send starting prompt with size %s", len(prompt))
                    responseMessage = await responses.handle_response(prompt)
                    channel = client.get_channel(int(config['discord_channel_id']))
                    await channel.send(responseMessage)
                    logger.info("Starting prompt response: %s",responseMessage)
                else:
                    logger.info("No Channel selected. Skip sending starting prompt.")
        else:
            logger.info("No %s. Skip sending starting prompt.",prompt_name)
    except Exception as e:
        logger.exception("Error while sending starting prompt: %s",e)


def run_discord_bot():
    client = aclient()

    @client.event
    async def on_ready():
        await send_start_prompt(client)
        await client.tree.sync()
        logger.info('%s is now running!',client.user)

    @client.event
    async def on_message(message):
        if message.author == client.user or message.author.bot:
            return
        with open('db.json', 'r') as file:
            data = json.load(file)
        if data.get(str(message.guild.id)) is None:
            return
        if str(message.channel.id) in data[str(message.guild.id)]:
            logger.info("\x1b[31m%s#%s\x1b[0m : '%s' (%s)", message.author.name, message.author.discriminator, message.content, message.channel.name)
            response = await responses.handle_response(message.content)
            await message.channel.send(response, reference=message)


    @client.tree.command(name="chat", description="Chat với con bot")
    async def chat(interaction: discord.Interaction, *, message: str):
        if interaction.user == client.user:
            return
        username = str(interaction.user)
        user_message = message
        channel = str(interaction.channel)
        logger.info(
            f"\x1b[31m{username}\x1b[0m : '{user_message}' ({channel})")
        await send_message(interaction, user_message)

    @client.tree.command(name="private", description="Chuyển sang chế độ riêng tư")
    async def private(interaction: discord.Interaction):
        global isPrivate
        await interaction.response.defer(ephemeral=False)
        if not isPrivate:
            isPrivate = not isPrivate
            logger.warning("\x1b[31mSwitch to private mode\x1b[0m")
            await interaction.followup.send("> **Info: Từ giờ, bot sẽ trả lời bạn ở chế độ riêng tư, chỉ có bạn mới xem được câu trả lời. Để chuyển lại chế độ public, gõ `/public`**")
        else:
            logger.info("You already on private mode!")
            await interaction.followup.send("> **Warn: Bạn đang ở chế độ riêng tư rồi. Để chuyển lại chế độ public, gõ `/public`**")

    @client.tree.command(name="public", description="Chuyển sang chế độ công khai")
    async def public(interaction: discord.Interaction):
        global isPrivate
        await interaction.response.defer(ephemeral=False)
        if isPrivate:
            isPrivate = not isPrivate
            await interaction.followup.send("> **Info: Từ giờ, mọi người sẽ thấy nội dung bot trả lời bạn. Để chuyển lại chế độ private, gõ `/private`**")
            logger.warning("\x1b[31mSwitch to public mode\x1b[0m")
        else:
            await interaction.followup.send("> **Warn: Bạn đang ở chế độ public rồi. Để chuyển lại chế độ private, gõ `/private`**")
            logger.info("You already on public mode!")

    @client.tree.command(name="reset", description="Xóa ký ức bot")
    async def reset(interaction: discord.Interaction):
        responses.chatbot.reset()
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send("> **Info: Ây da mất trí nhớ gòi, tui là đâu, đây là ai!.**")
        logger.warning(
            "\x1b[31mChatGPT bot has been successfully reset\x1b[0m")
        await send_start_prompt(client)


    @client.tree.command(name="auto", description="Lưu id kênh và tên kênh để bot trả lời tự động")
    async def auto(interaction: discord.Interaction):
        channel_id = str(interaction.channel.id)
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
            await interaction.followup.send(f"Kênh `{channel_name}` đã xóa khỏi list trả lời tự động của máy chủ `{guild_name}`.")
        else:
            channels[guild_id][channel_id] = channel_name
            with open('db.json', 'w') as f:
                json.dump(channels, f)
            await interaction.followup.send(f"Kênh `{channel_name}` đã thêm vào list trả lời tự động của máy chủ `{guild_name}`.")

    @client.tree.command(name="help", description="Trợ giúp")
    async def help(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)
        await interaction.followup.send(":star:**LỆNH CƠ BẢN** \n    `/chat [message]` Chat với bot!\n    `/public` Chuyển sang chế độ Public\n    `/private` Chuyển sang chế độ Private\n    `/auto` Lưu kênh chat để bot trả lời tự động\n    `/reset` Xóa ký ức bot")
        logger.info(
            "\x1b[31mSomeone need help!\x1b[0m")

    #TOKEN = config['discord_bot_token']
    TOKEN = os.environ['discord_bot_token']
    client.run(TOKEN)
