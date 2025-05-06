import os
import discord

import bot_commands as bc

from discord.ext import commands
from dotenv import load_dotenv
from ollamaherder import ollama_response, LLMStartup


# Load Env
load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")
BOT_APPLICATION_ID = os.getenv("APPLICATION_ID")
BOT_SERVER_ID = os.getenv("SERVER_ID")
BOT_DM_CHANNEL_ID = os.getenv("DM_CHANNEL_ID")
GMC_DISCUSSION_THREAD = os.getenv("GMCD_NOT_ALLOWED_THREAD")


# set discord intents
intents = discord.Intents.default()
intents.message_content = True

activity_status = bc.command_set_activity()

command_prefix = "$fb "
client = commands.Bot(
    command_prefix=command_prefix,
    intents=intents,
    activity=activity_status,
    status=discord.Status.online
)


class MyHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        help_message = """
For Full documentation see: [The Github Repo](<https://github.com/EvanSkiStudios/flukebot>)
Commands are issued like so: `$fb <command>`
```Here are my commands:
"""
        for cog, commands_list in mapping.items():
            for command in reversed(commands_list):
                help_message += f"`{command.name}` - {command.help or 'No description'}\n"
        help_message += "```"
        await self.get_destination().send(help_message)


# assign help command from bot_commands
client.help_command = MyHelpCommand()


# Startup LLM
LLMStartup()


# --------- BOT EVENTS ---------
@client.event
async def on_ready():
    # When the bot has logged in, call back
    print(f'We have logged in as {client.user}')


@client.event
async def on_disconnect():
    print(f"{client.user} disconnected!")


@client.event
async def on_connect():
    activity = bc.command_set_activity()
    new_status = discord.Status.online
    await client.change_presence(activity=activity, status=new_status)


@client.event
async def on_close():
    print(f"{client.user} closed!")


# ------- BOT COMMANDS ----------
@client.command(help="Changes Status to random or supplied custom")
async def status(ctx, *, arg=None):
    await bc.command_status(client, ctx, arg)


@client.command(help="Sets the conversation history between you and FlukeBot, depending on the argument")
async def history(ctx, arg=None):
    await bc.command_history(ctx, arg)


# ------- MESSAGE HANDLERS ---------
async def llm_chat(message, username, message_content):
    async with message.channel.typing():
        response = await ollama_response(client, username, message_content, False)

    if response == -1:
        return

    for i, part in enumerate(response):
        if not message.author.bot and i == 0:
            await message.reply(part)
        else:
            await message.channel.send(part)


@client.event
async def on_message(message):
    await client.process_commands(message)  # This line is required!

    message_lower = message.content.lower()
    username = message.author.name

    if message.author == client.user:
        return

    if message.mention_everyone:
        return

    if str(message.channel.id) == GMC_DISCUSSION_THREAD:
        return

    # DMs
    if isinstance(message.channel, discord.DMChannel):
        # print(f"{message_content}")

        if message_lower.find('save history') != -1:
            output = await bc.command_save_history(username)
            await message.channel.send(output)
            return

        if message_lower.find('delete history') != -1:
            output = await bc.command_delete_history(username)
            await message.channel.send(output)
            return

        if message_lower.find(command_prefix) == -1:
            await llm_chat(message, message.author.name, message_lower)
        return

# pack message content into tuple ref, to use later
# guild_id, channel_id, message_id = map(str, [message.author.guild.id, message.channel.id, message.id])
# message_channel_reference = (guild_id, channel_id, message_id)

    # replying to bot directly
    if message.reference:
        referenced_message = await message.channel.fetch_message(message.reference.message_id)
        if referenced_message.author == client.user:
            message_content = message_lower.replace(f"<@{BOT_APPLICATION_ID}>", "")
            await llm_chat(message, message.author.name, message_content)
            return

    # Pinging the bot
    if message_lower.find(str(BOT_APPLICATION_ID)) != -1:
        message_content = message_lower.replace(f"<@{BOT_APPLICATION_ID}> ", "")
        await llm_chat(message, message.author.name, message_content)
        return

    # if the message includes "flukebot" it will trigger and run the code
    if message_lower.find('flukebot') != -1:
        await llm_chat(message, message.author.name, message_lower)
        return


# Startup discord Bot
client.run(BOT_TOKEN)
