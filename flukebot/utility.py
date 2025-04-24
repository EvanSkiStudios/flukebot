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


def split_response(response, max_len=2000):
    chunks = []
    while len(response) > max_len:
        # Find the last space or line break within the first max_len characters
        split_index = max(response.rfind(' ', 0, max_len), response.rfind('\n', 0, max_len))
        if split_index == -1:
            # If no space or newline is found, just split at max_len
            split_index = max_len
        chunks.append(response[:split_index].rstrip())
        response = response[split_index:].lstrip()
    if response:
        chunks.append(response)
    return chunks
