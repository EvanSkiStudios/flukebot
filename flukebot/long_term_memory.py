import os
import json
import discord
import asyncio


# get location of memories
running_dir = os.path.dirname(os.path.realpath(__file__))
memories_location = str(running_dir) + "/memories/"


def convo_delete_history(username):
    user_conversation_memory_file = os.path.join(memories_location, f"{username}.json")

    if os.path.exists(user_conversation_memory_file):
        os.remove(user_conversation_memory_file)
        return 1
    else:
        return -1


def convo_write_memories(username, conversation_data, message_channel_reference):
    user_conversation_memory_file = os.path.join(memories_location, f"{username}.json")

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


async def fetch_discord_message(client, message_reference, retries=3, backoff=1.0):
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
        if e.status == 429 and retries > 0:
            print(f"⏳ Rate limit hit (429). Retrying in {backoff:.1f} seconds...")
            await asyncio.sleep(backoff)
            return await fetch_discord_message(client, message_reference, retries - 1, backoff * 2)
        else:
            print(f"⚠️ HTTP error occurred: {e} (status {e.status})")

    return -1  # Return None if message couldn't be fetched


# BATCH_SIZE = 10  # How many items to fetch at once
# DELAY_BETWEEN_BATCHES = 1  # Seconds to wait between each batch
# TODO - This works but god is it slow, we need to figure out how to work around the rate limiting


async def memory_fetch_user_conversations(client, username):
    user_conversation_memory_file = os.path.join(memories_location, f"{username}.json")

    if not os.path.exists(user_conversation_memory_file):
        return []

    # Load the message history
    with open(user_conversation_memory_file, "r") as f:
        full_history = json.load(f)
        message_history_references = full_history[-20:]  # Only keep the last 20

    async def process_item(key, item):
        print(f"GETTING MEMORY: {key + 1} / {len(message_history_references)}")

        if item.get("role") != "user":
            return item

        # Safely parse JSON content
        content_str = item["content"]
        try:
            content = json.loads(content_str if isinstance(content_str, str) else json.dumps(content_str))
        except json.JSONDecodeError:
            # print(f"❌❌ Json Error for Memory: {key + 1}\n{item}")
            # return item  # Skip or handle error as needed
            fixed_data = content_str.replace("'", '"')
            content = json.loads(fixed_data if isinstance(fixed_data, str) else json.dumps(fixed_data))

        message_reference = (str(content.get("channel_id")), str(content.get("message_id")))
        fetched_message = await fetch_discord_message(client, message_reference)

        if fetched_message != -1:
            item["content"] = fetched_message
        return item

    # Process all items concurrently
    processed_items = await asyncio.gather(
        *(process_item(i, item) for i, item in enumerate(message_history_references)))

    print(f"✅ Finished processing {len(processed_items)} memories")

    return processed_items
