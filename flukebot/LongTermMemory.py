import os
import json
import discord

import error_handler


# get location of memories
running_dir = os.path.dirname(os.path.realpath(__file__))
memories_location = str(running_dir) + "/memories/"


def convo_delete_history(username):
    user_conversation_memory_file = memories_location + f"{username}.json"

    if os.path.exists(user_conversation_memory_file):
        os.remove(user_conversation_memory_file)
        return 1
    else:
        return -1


def convo_write_memories(username, conversation_data, message_channel_reference):
    user_conversation_memory_file = memories_location + f"{username}.json"

    # unpack tuple ref
    guild_id, channel_id, message_id = message_channel_reference

    user_message_info = {"channel_id": channel_id, "message_id": message_id}
    conversation_data[0]["content"] = str(user_message_info)

    if os.path.exists(user_conversation_memory_file):
        print(f"☁️ Memories found for: {username}")

        # Step 1: Read the original JSON file
        with open(user_conversation_memory_file, "r") as f:
            message_history_references = json.load(f)  # Loads existing list

        # Step 2: Append new info
        message_history_references.extend(conversation_data)
        # print(f"Memories: {message_history_references}")

        # Step 3: Save the updated data back to the same file
        with open(user_conversation_memory_file, "w") as f:
            json.dump(message_history_references, f, indent=4)  # Pretty print is optional

        print(f"✅ Memories Saved")

    else:
        print(f"⚠️ Creating New Memories for: {username}")
        with open(user_conversation_memory_file, "w") as f:
            json.dump(conversation_data, f)
        f.close()


async def fetch_discord_message(client, message_reference):
    # unpack tuple ref
    channel_id, message_id = message_reference
    try:
        channel = await client.fetch_channel(channel_id)
        message = await channel.fetch_message(message_id)
        return message.content.lower()

    except discord.NotFound:
        print(f"❌ Message {message_id} or channel not found. Skipping")
    except discord.Forbidden:
        print(f"🚫 Bot doesn't have permission to access the channel or  {message_id}.")
    except discord.HTTPException as e:
        print(f"⚠️ A general HTTP error occurred: {e}")

    return -1  # Return None if message couldn't be fetched


async def memory_fetch_user_conversations(client, username, llm_current_chatter, current_llm_history, message_channel_reference):

    # check if new user already has history
    user_conversation_memory_file = memories_location + f"{username}.json"
    if os.path.exists(user_conversation_memory_file):
        with open(user_conversation_memory_file, "r") as f:
            message_history_references = json.load(f)

        for (key, item) in enumerate(message_history_references):
            print(f"GETTING MEMORY: {key} \n{key}\n{item}\n")
            # print(f"GETTING MEMORY: {key}")

            if item["role"] == "user":
                # print(f"MEMORY IS USER:\n{key}\n{item}\n")

                # Extract the necessary values
                # the dict is stored as a string, so we need to convert it back to a dict
                fixed_content = item["content"].replace("'", '"')
                item["content"] = json.loads(fixed_content)

                channel_id, message_id = map(str, [item["content"]["channel_id"], item["content"]["message_id"]])
                message_reference = (channel_id, message_id)

                # Fetch the message from Discord
                fetched_message = await fetch_discord_message(client, message_reference)

                # Check if the fetch was successful (assuming -1 means failure)
                if fetched_message != -1:
                    # Replace the content in the original dictionary
                    item["content"] = fetched_message

                    # Optionally, update the dictionary with the new value if you want to keep the reference
                    message_history_references[key] = item
        return message_history_references

    else:
        return []
    # if no history file just return an empty list
