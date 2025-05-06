import json
import os

import discord

from discord.ext import commands

from dotenv import load_dotenv

from flukebot_filter import LLM_Filter_Message
from long_term_memory import convo_delete_history
from ollamaherder import LLMStartup
from ollamaherder import LLMConverse

from utility import set_activity, split_response


# Startup LLM
LLMStartup()


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


@client.event
async def on_disconnect():
    print(f"{client.user} disconnected!")


@client.event
async def on_connect():
    activity_status = set_activity()
    new_status = discord.Status.online
    await client.change_presence(activity=activity_status, status=new_status)


@client.event
async def on_close():
    print(f"{client.user} closed!")


@client.command(help="Changes Status Presence")
async def changestatus(ctx):
    print(f"Command issued: Change Status")

    new_activity_status = set_activity()
    await client.change_presence(activity=new_activity_status)

    print(f"Changed Status to: {new_activity_status}")

    await ctx.send("Changed Status")


@client.command(help="Changes Status To Custom")
async def status(ctx, arg):
    print(f"Command issued: Status")

    await client.change_presence(activity=discord.CustomActivity(name=f"{arg}", emoji=' '))

    await ctx.send(f"Status is now {arg}")


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


@client.command(help="Allows Conversation History between you and FlukeBot to be saved")
async def savehistory(ctx):
    print(f"Command issued: SaveHistory")
    user = ctx.author.id

    information_message = """
In order to save conversation history I require consent to save your discord messages.
Only the messages you send to me will be saved and only used to remember details and conversation history.
Your conversation history is never sold or given to anyone or any 3rd party.
At any point you can run the command "$fb clearhistory" to remove your conversation history.
Please send me a DM with "save history" to opt in. or "delete history" to opt out.
"""
    await ctx.reply(ctx.author.mention + information_message)


async def command_save_history(user):
    # get location of consent file
    running_dir = os.path.dirname(os.path.realpath(__file__))
    file_location = str(running_dir) + "/memories/"
    consent_file = os.path.join(file_location, "__consent_users.json")

    if not os.path.exists(consent_file):
        print("❌❌❌ Can not find user consent file!!")
        return "unexpected Error Please Try again later"

    # Load the message history
    with open(consent_file, "r") as f:
        file_data = json.load(f)

    # add user to list
    if str(user) not in file_data:
        file_data.append(str(user))

        # Save the updated data back to the file
        with open(consent_file, 'w') as file:
            json.dump(file_data, file, indent=4)

    return (
        "Your conversation history will now be saved.\nAt anytime send me 'delete history' to opt out.\nPlease also "
        "see the command to delete conversation history by using '$fb help'")


async def command_delete_history(user):
    # get location of consent file
    running_dir = os.path.dirname(os.path.realpath(__file__))
    file_location = str(running_dir) + "/memories/"
    consent_file = os.path.join(file_location, "__consent_users.json")

    if not os.path.exists(consent_file):
        print("❌❌❌ Can not find user consent file!!")
        return "unexpected Error Please Try again later"

    # Load the existing data
    with open(consent_file, 'r') as file:
        data = json.load(file)

    # Remove "dave" if it exists
    if str(user) in data:
        data.remove(str(user))

    # Save the updated data back to the file
    with open(consent_file, 'w') as file:
        json.dump(data, file, indent=4)

    return_message = "You have been removed from the history collection list"

    outcome = convo_delete_history(user)
    outcome_message = "Unknown Error with current conversation history, Try again later!"

    if outcome == 1:
        outcome_message = "Conversation History has been deleted"

    if outcome == -1:
        outcome_message = ("Conversation History might not exist or an Error Occurred, Please Contact Evanski to have "
                           "your history deleted")

    return return_message + "\n" + outcome_message


async def ollama_response(bot_client, message_author_name, message_content, filtered=False):
    output_bool = True
    if filtered:
        dictation = await LLM_Filter_Message(message_content)
        print(f"\n{message_content}")
        print(f"Directed to Flukebot = {dictation["output"]}")
        print(f"{dictation["content"]}\n")

        output_bool = dictation["output"]

    if output_bool:
        LLMResponse = await LLMConverse(bot_client, message_author_name, message_content)
        response = (LLMResponse
                    .replace("'", "\'")
                    .replace("evanski_", "Evanski")
                    .replace("Evanski_", "Evanski")
                    )

        # discord message limit
        if len(response) > 2000:
            response = split_response(response)
        else:
            response = [response]

        return response

    return -1


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
            output = await command_save_history(username)
            await message.channel.send(output)
            return

        if message_lower.find('delete history') != -1:
            output = await command_delete_history(username)
            await message.channel.send(output)
            return

        async with message.channel.typing():  # displays "is typing" status
            response = await ollama_response(client, message.author.name, message_lower)

        if response == -1:
            return

        for i, part in enumerate(response):
            await message.channel.send(part)

        return

    # if message.author.bot:

    # pack message content into tuple ref, to use later
    guild_id, channel_id, message_id = map(str, [message.author.guild.id, message.channel.id, message.id])
    message_channel_reference = (guild_id, channel_id, message_id)

    # replying to bot directly
    if message.reference:
        referenced_message = await message.channel.fetch_message(message.reference.message_id)
        if referenced_message.author == client.user:
            message_content = message.content.lower()
            message_content = message_content.replace(f"<@{BOT_APPLICATION_ID}>", "")

            # displays "is typing" status
            async with message.channel.typing():
                response = await ollama_response(client, username, message_content)

            if response == -1:
                return

            for i, part in enumerate(response):
                await message.channel.send(part)

            return

    # Pinging the bot
    if message_lower.find(str(BOT_APPLICATION_ID)) != -1:
        message_content = message.content.lower()
        message_content = message_content.replace(f"<@{BOT_APPLICATION_ID}> ", "")

        async with message.channel.typing():
            response = await ollama_response(client, username, message_content)

        if response == -1:
            return

        for i, part in enumerate(response):
            await message.channel.send(part)
            # await message.reply(part)

        return

    # if the message includes "flukebot" it will trigger and run the code
    if message_lower.find('flukebot') != -1:
        message_content = message.content.lower()

        async with message.channel.typing():
            response = await ollama_response(client, username, message_content, False)

        if response == -1:
            return

        for i, part in enumerate(response):
            # await message.channel.send(part)

            if not message.author.bot and i == 0:
                await message.reply(part)
            else:
                await message.channel.send(part)

        return

# Login
client.run(BOT_TOKEN)


