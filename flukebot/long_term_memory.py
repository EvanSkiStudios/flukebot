import os
import json


# get location of memories
running_dir = os.path.dirname(os.path.realpath(__file__))
memories_location = str(running_dir) + "\\memories\\"

# details
character_details_location = memories_location + "\\meet_the_robinsons\\"


def random_factoids():
    # get location of facts
    facts_location = os.path.join(memories_location, "__things_you_know.json")

    if not os.path.exists(facts_location):
        print("❌❌❌ Can not find Facts file!!")
        return ""

        # Load the existing data
    with open(facts_location, 'r') as file:
        data = json.load(file)

    result = ''.join(line .strip() for line in data)

    factoids = "Here is a few random facts you know: " + result

    people_we_know = ''
    for filename in os.listdir(character_details_location):
        file_path = os.path.join(character_details_location, filename)
        if os.path.isfile(file_path):
            with open(file_path, 'r') as file:
                contents = file.read()
                try:
                    facts = json.loads(contents)  # Convert JSON string to Python list
                    joined_facts = "\n- ".join(facts)
                    info = f"\nThis is what you know about {filename.replace('.json', '')}:\n- {joined_facts}"
                    people_we_know += info
                except json.JSONDecodeError:
                    print(f"Warning: Could not parse {filename} as JSON.")

    return factoids + people_we_know


def convo_delete_history(username):
    user_conversation_memory_file = os.path.join(memories_location, f"{username}.json")

    if os.path.exists(user_conversation_memory_file):
        os.remove(user_conversation_memory_file)
        return 1
    else:
        return -1


def convo_write_memories(username, conversation_data):
    consent_file = os.path.join(memories_location, "__consent_users.json")

    if not os.path.exists(consent_file):
        print("❌❌❌ Can not find user consent file!!")
        return

    # Load the existing data
    with open(consent_file, 'r') as file:
        data = json.load(file)

    # Check if user is in consent file
    if str(username) not in data:
        return

    user_conversation_memory_file = os.path.join(memories_location, f"{username}.json")

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


async def memory_fetch_user_conversations(username):
    user_conversation_memory_file = os.path.join(memories_location, f"{username}.json")

    if not os.path.exists(user_conversation_memory_file):
        print(f"⚠️ No memories found for {username}")
        return []

    # Load the message history
    with open(user_conversation_memory_file, "r") as f:
        message_history_references = json.load(f)
        # print(f"{message_history_references}")
        print(f"✅ Finished processing memories")
        return message_history_references
