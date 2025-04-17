import os
import discord

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

client = discord.Client(command_prefix="$", intents=intents)


@client.event
async def on_ready():
    # When the bot has logged in, call back
    print(f'We have logged in as {client.user}')


async def fetch_discord_message(message_reference):
    # unpack tuple ref
    guild_id, channel_id, message_id = message_reference

    channel = await client.fetch_channel(channel_id)
    message = await channel.fetch_message(message_id)

    return message


# very basic message detection
@client.event
async def on_message(message):
    # print(f' RECEIVED MESSAGE: {message}')

    # pack message content into tuple ref, to use later
    guild_id, channel_id, message_id = map(str, [message.author.guild.id, message.channel.id, message.id])
    message_channel_reference = (guild_id, channel_id, message_id)

    message_lower = message.content.lower()

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


