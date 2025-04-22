import random
import discord


def set_activity():
    activity = discord.Game(name="Hello Kitty Island Adventure")

    random_integer = random.randint(1, 5)

    match random_integer:

        case 2:
            # Setting `Streaming ` status
            activity = discord.Streaming(name="Programming an AI LLM", url="https://www.twitch.tv/evanskistudios")

        case 3:
            # Setting `Listening ` status
            activity = discord.Activity(type=discord.ActivityType.listening, name='Harry Dacre - "Daisy Bell (Bicycle Built for Two)"')

        case 4:
            # Setting `Watching ` status
            activity = discord.Activity(type=discord.ActivityType.watching, name="Shrek 7")

        case 5:
            activity = None  # Clear status

    return activity
