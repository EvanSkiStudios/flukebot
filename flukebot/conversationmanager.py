import os


async def fetch_discord_message(client, message_reference):
    # unpack tuple ref
    guild_id, channel_id, message_id = message_reference

    channel = await client.fetch_channel(channel_id)
    message = await channel.fetch_message(message_id)

    return message


# get location of memories
running_dir = os.path.dirname(os.path.realpath(__file__))
memories_location = str(running_dir) + "/memories/"


# "a" - Append - will append to the end of the file
# "w" - Write - will overwrite any existing content


def convo_write_memories(username, conversation_data):
    f = open(memories_location + f"{username}.txt", "a")
    f.write(str(conversation_data))
    f.close()


# open and read the file after the appending:
# f = open(memories_location+"test.txt", "r")
# print(f.read())

