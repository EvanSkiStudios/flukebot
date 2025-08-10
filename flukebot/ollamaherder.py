import json
import asyncio

import ollama
from ollama import Client, chat, ChatResponse, AsyncClient

from Tools.gemma_vision import download_image, image_cleanup
from flukebot_ruleset import flukebot_personality
from long_term_memory import convo_write_memories, memory_fetch_user_conversations, random_factoids
from meet_the_robinsons import fetch_chatter_description
from utility import split_response, current_date_time
from pathlib import Path

# import from ruleset must be made a global variable
flukebot_rules = flukebot_personality

# memories
llm_current_user_speaking_too = None
llm_current_user_conversation_history = []
llm_session_memory_cache = {}
current_chatter_character_information = ""


def get_llm_state_snapshot():
    return (
        llm_current_user_conversation_history,
        llm_current_user_speaking_too,
        llm_session_memory_cache,
        current_chatter_character_information
    )


# model settings for easy swapping
flukebot_model_name = 'flukebot_llama3.2'
flukebot_ollama_model = 'llama3.2'


# === Setup ===
def LLMStartup():
    client = Client()
    response = client.create(
        model=flukebot_model_name,
        from_=flukebot_ollama_model,
        system=flukebot_rules,
        stream=False,
    )
    print(f"# Client: {response.status}")
    return get_llm_state_snapshot()


# === Main Entry Point ===
async def ollama_response(bot_client, message_author_name, message_author_nickname, message_content, attachment_url, attachments):
    llm_response = None

    if attachment_url:
        loop = asyncio.get_event_loop()
        image_file_name = await loop.run_in_executor(None, download_image, attachment_url)

        if image_file_name:
            llm_response = await gemma3_image_recognition(
                bot_client, message_author_name, message_author_nickname, message_content, image_file_name, attachments
            )
        else:
            print("IMAGE ERROR")

    if llm_response is None:  # fallback to text-only LLM
        llm_response = await LLMConverse(
            bot_client, message_author_name, message_author_nickname, message_content
        )

    cleaned = llm_response.replace("'", "\\'")
    return split_response(cleaned)


# === Core Logic ===
async def LLMConverse(client, user_name, user_nickname, user_input):
    # check who we are currently talking too - if someone new is talking to us, fetch their memories
    # if it's a different user, cache the current history to file the swap out the memories
    await switch_current_user_speaking_too(user_name)

    system_prompt = build_system_prompt(user_name, user_nickname)
    full_prompt = [{"role": "system", "content": system_prompt + "Here is what they have said to you: "}] \
                  + llm_current_user_conversation_history \
                  + [{"role": "user", "name": user_name, "content": user_input}]

    # This is where we get some lag, and most likely the discord api time-outs, im not sure what to do with that
    # response = chat(model=flukebot_model_name, messages=full_prompt)

    # should prevent discord heartbeat from complaining we are taking too long
    response = await asyncio.to_thread(
        chat,
        model=flukebot_model_name,
        messages=full_prompt
    )

    # Add the response to the messages to maintain the history
    new_chat_entries = [
        {"role": "user", "name": user_name, "content": user_input},
        {"role": "assistant", "content": response.message.content},
    ]
    update_conversation_history(user_name, new_chat_entries)

    # Debug Console Output
    print("\n===================================\n")
    print(f"{user_name} REPLY:\n" + user_input + '\n')
    print("RESPONSE:\n" + response.message.content)
    print("\n===================================\n")

    # return the message to main script
    return response.message.content


async def gemma3_image_recognition(client, user_name, user_nickname, user_input, image_file_name, attachments):
    await switch_current_user_speaking_too(user_name)

    # Go one directory up
    parent_dir = Path(__file__).resolve().parent
    path = parent_dir / 'images' / image_file_name

    print(f'Analyzing image ({image_file_name})...\n')
    print(attachments)
    print('\n')

    system_prompt = build_system_prompt(user_name, user_nickname)
    full_prompt = [{"role": "system", "content": system_prompt + "Here is what they have said to you: "}] \
                  + llm_current_user_conversation_history \


    response = await asyncio.to_thread(
        chat,
        model='gemma3',
        messages=full_prompt + [{"role": "user", "name": user_name, "content": user_input, 'images': [path]}]
        # options={'temperature': 0},  # Make responses more deterministic
    )

    output = response.message.content
    output = output.replace("'", "").strip()

    # Add the response to the messages to maintain the history
    new_chat_entries = [
        {"role": "user", "name": user_name, "content": user_input, "attachments": str(attachments)},
        {"role": "assistant", "content": output},
    ]
    update_conversation_history(user_name, new_chat_entries)

    # Debug Console Output
    print("\n===================================\n")
    print(f"{user_name} REPLY:\n" + user_input + '\n')
    print("RESPONSE:\n" + output)
    print("\n===================================\n")

    # clean up image
    image_cleanup(image_file_name)

    # return the message to main script
    return output


# === Helpers ===
async def switch_current_user_speaking_too(user_name):
    global llm_current_user_speaking_too
    global llm_current_user_conversation_history
    global current_chatter_character_information

    if user_name == llm_current_user_speaking_too:
        return

    print(f"⚠️ SWITCHING CONVERSER FROM {llm_current_user_speaking_too} > {user_name}")

    # check if we have already spoken to this person this session
    cached = llm_session_memory_cache.get(user_name)
    if cached:
        print(f"✅ FOUND USER CACHE FOR {user_name}")
        llm_current_user_conversation_history[:] = json.loads(cached)
    else:
        llm_current_user_conversation_history[:] = await memory_fetch_user_conversations(user_name)

    current_chatter_character_information = fetch_chatter_description(user_name)
    llm_current_user_speaking_too = user_name


def build_system_prompt(user_name, user_nickname):
    factoids = random_factoids()
    current_time = current_date_time()
    return (
            flukebot_rules + "\n" +
            factoids + "\n" +
            current_time + "\n" +
            f"You are currently talking to {user_name}. Their name is {user_name}.\n" +
            f"Their display name is {user_nickname}.\n" +
            f"If {user_name} asks what their name is, use their display name.\n" +
            current_chatter_character_information
    )


def update_conversation_history(user_name, new_messages):
    llm_current_user_conversation_history.extend(new_messages)
    llm_session_memory_cache[user_name] = json.dumps(llm_current_user_conversation_history)
    convo_write_memories(user_name, new_messages)
