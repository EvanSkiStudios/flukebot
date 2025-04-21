import os
import json


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


def convo_write_memories(username, conversation_data, message_channel_reference):
    user_conversation_memory_file = memories_location + f"{username}.json"

    # unpack tuple ref
    guild_id, channel_id, message_id = message_channel_reference

    if os.path.exists(user_conversation_memory_file):

        # Step 1: Read the original JSON file
        with open(user_conversation_memory_file, "r") as f:
            message_history_references = json.load(f)  # This gives you a list or dict depending on your file

        # Step 2: Append new info
        message_history_references.extend(conversation_data)  # Adds each item individually

        # Step 3: Clear the original file (optional)
        with open(user_conversation_memory_file, "w") as f:
            f.truncate()  # Clears the file contents

        # Step 4: Save the updated data to a new file
        with open(user_conversation_memory_file, "w") as f:
            json.dump(message_history_references, f)
        f.close()

    else:
        with open(user_conversation_memory_file, "w") as f:
            json.dump(conversation_data, f)
        f.close()


def memory_fetch_user_conversations(client, username):
    # todo get conversation history and convert it with fetch conversation
    # fetch_discord_message

    f = open(memories_location + f"{username}.txt", "r")
    message_history_references = f.read()
