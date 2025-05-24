import json
from ollama import Client, chat, ChatResponse
from flukebot_ruleset import flukebot_personality
from long_term_memory import convo_write_memories, memory_fetch_user_conversations
from meet_the_robinsons import fetch_chatter_description
from utility import split_response

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


# === Setup ===
def LLMStartup():
    client = Client()
    response = client.create(
        model='flukebot',
        from_='llama3.2',
        system=flukebot_rules,
        stream=False,
    )
    print(f"# Client: {response.status}")
    return get_llm_state_snapshot()


# === Main Entry Point ===
async def ollama_response(bot_client, message_author_name, message_content):
    llm_response = await LLMConverse(bot_client, message_author_name, message_content)
    print(f"HAVE RESPONSE, CLEANING AND RETURNING")
    cleaned = (
        llm_response.replace("'", "\'")
        .replace("evanski_", "Evanski")
        .replace("Evanski_", "Evanski")
    )
    return split_response(cleaned)


# === Core Logic ===
async def LLMConverse(client, user_name, user_input):
    # check who we are currently talking too - if someone new is talking to us, fetch their memories
    # if it's a different user, cache the current history to file the swap out the memories
    await switch_current_user_speaking_too(user_name)

    system_prompt = build_system_prompt(user_name)
    full_prompt = [{"role": "system", "content": system_prompt + "Here is what they have said to you: "}] \
                  + llm_current_user_conversation_history \
                  + [{"role": "user", "name": user_name, "content": user_input}]

    # This is where we get some lag, and most likely the discord api time outs, im not sure what to do with that
    response = chat(model='flukebot', messages=full_prompt)

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


def build_system_prompt(user_name):
    return (
            flukebot_rules +
            f"You are currently talking to {user_name}. Their name is {user_name}.\n"
            f"If the person you are chatting with asks what their name is, it is {user_name}.\n"
            f"If {user_name} mentions flukebot, assume they mean you.\n"
            + current_chatter_character_information
    )


def update_conversation_history(user_name, new_messages):
    llm_current_user_conversation_history.extend(new_messages)
    llm_session_memory_cache[user_name] = json.dumps(llm_current_user_conversation_history)
    convo_write_memories(user_name, new_messages)
