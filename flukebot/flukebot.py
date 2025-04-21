import os
import discord

from discord.ext import commands

from dotenv import load_dotenv

from LongTermMemory import convo_delete_history
from ollamaherder import LLMStartup
from ollamaherder import LLMConverse

from Utility import set_activity

# TODO - Create a Error handler so the bot doesnt just silently crash and the discord bot stays online

# Startup LLM
LLMStartup()

# Load Env
load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")
BOT_APPLICATION_ID = os.getenv("APPLICATION_ID")
BOT_SERVER_ID = os.getenv("SERVER_ID")
GMC_DISCUSSION_THREAD = os.getenv("GMCD_Discussion_Thread_ID")

# set discord intents
intents = discord.Intents.default()
intents.message_content = True

activity_status = set_activity()

# client = discord.Client(intents=intents)
client = commands.Bot(command_prefix="$fb ", intents=intents, activity=activity_status, status=discord.Status.online)


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


# Then assign it to your bot
client.help_command = MyHelpCommand()


@client.event
async def on_ready():
    # When the bot has logged in, call back
    print(f'We have logged in as {client.user}')


@client.command(help="Changes Status Presence")
async def changestatus(ctx):
    print(f"Command issued: Change Status")

    new_activity_status = set_activity()
    await client.change_presence(activity=new_activity_status)

    print(f"Changed Status to: {new_activity_status}")

    await ctx.send("Changed Status")


@client.command(help="Removes all Conversation History between you and FlukeBot")
async def clearhistory(ctx):
    print(f"Command issued: clearhistory")
    user = ctx.author.name

    outcome = convo_delete_history(user)
    outcome_message = "Unknown Error, Try again later!"

    if outcome == 1:
        print(f"Deleted Conversation history for {user}")
        outcome_message = f"Deleted Conversation history for {user}"

    if outcome == -1:
        print(f"No Conversation history for {user}")
        outcome_message = f"No Conversation history for {user}"

    await ctx.send(outcome_message)


@client.event
async def on_message(message):
    await client.process_commands(message)  # This line is required!

    # print(f' RECEIVED MESSAGE: {message}')

    # pack message content into tuple ref, to use later
    guild_id, channel_id, message_id = map(str, [message.author.guild.id, message.channel.id, message.id])
    message_channel_reference = (guild_id, channel_id, message_id)

    message_lower = message.content.lower()

    if message.author == client.user:
        return

    if message.mention_everyone:
        return

    if message.channel.id == GMC_DISCUSSION_THREAD:
        return

    # TODO - Wire replying and pinging the bot to be considered speaking to it and wanting the LLM

    # replying to bot directly
    if message.reference:
        referenced_message = await message.channel.fetch_message(message.reference.message_id)
        if referenced_message.author == client.user:
            # We have confirmed the replayed to message is from EvanJelly
            await message.channel.send('Test reply successful')
            return

    # Pinging the bot
    if message_lower.find("@" + str(BOT_APPLICATION_ID)) != -1:
        await message.channel.send('Ping Pong!')
        return

    # test of general message getting
    if message_lower.find('evanjelly') != -1:
        if message.content.lower().find('language') != -1:
            await message.channel.send('Im powered by snakes! :snake:')
            return

    # if the message includes "flukebot" it will trigger and run the code
    if message_lower.find('flukebot') != -1:

        LLMResponse = await LLMConverse(client, message.author.name, message.content.lower(), message_channel_reference)

        response = LLMResponse.replace("'", "\'")

        await message.channel.send(response)
        return

# Login
client.run(BOT_TOKEN)

