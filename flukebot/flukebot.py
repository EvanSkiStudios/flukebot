import asyncio
import os
import discord

import bot_commands as bc

from discord.ext import commands
from dotenv import load_dotenv

from flukebot_emoji import llm_emoji_react_to_message, gather_server_emotes
from ollamaherder import ollama_response, LLMStartup


# Load Env
load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")
BOT_APPLICATION_ID = os.getenv("APPLICATION_ID")
BOT_SERVER_ID = os.getenv("GMCD_SERVER_ID")
BOT_DM_CHANNEL_ID = os.getenv("DM_CHANNEL_ID")
GMC_DISCUSSION_THREAD = os.getenv("GMCD_NOT_ALLOWED_THREAD_D")
GMC_NO_CONTEXT_THREAD = os.getenv("GMCD_NOT_ALLOWED_THREAD_NC")
BOT_TEST_SERVER_ID = os.getenv("TEST_SERVER_ID")


# set discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.emojis = True
intents.emojis_and_stickers = True

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
Commands are issued like so: `$fb <command> <argument>`
```Here are my commands:
"""
        for cog, commands_list in mapping.items():
            for command in commands_list:
                help_message += f"`{command.name}` - {command.help or 'No description'}\n"
        help_message += "```"
        await self.get_destination().send(help_message)


# assign help command from bot_commands
client.help_command = MyHelpCommand()


# Startup LLM
LLMStartup()

emote_dict = {}

# --------- BOT EVENTS ---------
@client.event
async def on_ready():
    # When the bot has logged in, call back
    print(f'We have logged in as {client.user}')
    global emote_dict
    emote_dict = gather_server_emotes(client, BOT_SERVER_ID, BOT_TEST_SERVER_ID)


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
        response = await ollama_response(client, username, message_content)

    if response == -1:
        return

    for i, part in enumerate(response):
        if not message.author.bot and i == 0:
            await message.reply(part)
        else:
            await message.channel.send(part)


async def react_to_messages(message, message_lower):
    global emote_dict
    # reaction
    reaction = await llm_emoji_react_to_message(message_lower, emote_dict)
    # discord limits by 20 reactions
    reaction = reaction[:20]
    for emoji in reaction:
        if emoji.find('no reaction') == -1:
            await message.add_reaction(emoji)


@client.event
async def on_message(message):
    await client.process_commands(message)  # This line is required!

    message_lower = message.content.lower()
    username = message.author.name

    if message.author == client.user:
        return

    if message.mention_everyone:
        return

    if message_lower.find(command_prefix) != -1:
        return

    # noinspection PyAsyncCall
    asyncio.create_task(react_to_messages(message, message_lower))
    # task.add_done_callback(lambda t: t.exception())  # Prevent warning if task crashes
    #  -- Its fine we don't care if it returns

    if str(message.channel.id) == GMC_DISCUSSION_THREAD:
        return

    if str(message.channel.id) == GMC_NO_CONTEXT_THREAD:
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

        await llm_chat(message, message.author.name, message_lower)
        return

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
