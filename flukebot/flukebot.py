import os
import discord

from discord.ext import commands
# from discord.ext.commands import Bot

from dotenv import load_dotenv

from ollamaherder import LLMStartup
from ollamaherder import LLMConverse

# Startup LLM
LLMStartup()

# Load Env
load_dotenv()
BOT_TOKEN = os.getenv("TOKEN")
BOT_APPLICATION_ID = os.getenv("APPLICATION_ID")
BOT_SERVER_ID = os.getenv("SERVER_ID")

# set discord intents
intents = discord.Intents.default()
intents.message_content = True

# client = discord.Client(intents=intents)
client = commands.Bot(command_prefix="$fb ", intents=intents)


class MyHelpCommand(commands.HelpCommand):
    async def send_bot_help(self, mapping):
        help_message = """
        For Full documentation see: [The Github Repo](https://github.com/EvanSkiStudios/flukebot)\n
        Commands are prefixed with "$fb "\n
        ```Here are my commands:\n"
        """
        for cog, commands_list in mapping.items():
            for command in commands_list:
                help_message += f"`{command.name}` - {command.help or 'No description'}\n"
        help_message += "```"
        await self.get_destination().send(help_message)


# Then assign it to your bot
client.help_command = MyHelpCommand()


@client.event
async def on_ready():
    # When the bot has logged in, call back
    print(f'We have logged in as {client.user}')


@client.command(help="Replies with pong.")
async def ping(ctx):
    await ctx.send("pong")


async def fetch_discord_message(message_reference):
    # unpack tuple ref
    guild_id, channel_id, message_id = message_reference

    channel = await client.fetch_channel(channel_id)
    message = await channel.fetch_message(message_id)

    return message

@client.event
async def on_message(message):
    await client.process_commands(message)  # This line is required!

    # print(f' RECEIVED MESSAGE: {message}')

    # pack message content into tuple ref, to use later
    guild_id, channel_id, message_id = map(str, [message.author.guild.id, message.channel.id, message.id])
    message_channel_reference = (guild_id, channel_id, message_id)

    message_lower = message.content.lower()

    # TODO-- ignore discussion thread of main bot-arena channel

    if message.author == client.user:
        return

    if message.mention_everyone:
        return

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

    # command but not really all that necessary with above
    if message.content.startswith('$hello'):
        await message.channel.send('Hello!')
        return

    # basic command, if the message includes "flukebot" it will trigger and run the code
    if message_lower.find('flukebot') != -1:
        LLMResponse = "" + LLMConverse(message.author.name, message.content.lower())

        response = "" + LLMResponse.replace("'", "\'")

        await message.channel.send(response)
        return

# Login
client.run(BOT_TOKEN)


