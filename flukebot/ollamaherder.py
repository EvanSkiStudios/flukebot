import json

import ollama

from ollama import chat
from ollama import Client

from flukebot_ruleset import flukebot_personality
from long_term_memory import convo_write_memories, memory_fetch_user_conversations

from flukebot_tools import google_search_tool

flukebot_rules = flukebot_personality

# memories
LLM_current_chatter = None
LLM_Current_Conversation_History = []
LLM_memory_cache = {}


def LLMStartup():
    global LLM_Current_Conversation_History, LLM_current_chatter, flukebot_rules, LLM_memory_cache

    client = Client()
    response = client.create(
        model='flukebot',
        from_='llama3.2',
        system=flukebot_rules,
        stream=False,
    )
    print(f"# Client: {response.status}")
    return LLM_Current_Conversation_History, LLM_current_chatter, LLM_memory_cache


async def LLMConverse(client, user_name, user_input, message_channel_reference):
    global LLM_Current_Conversation_History, LLM_current_chatter, flukebot_rules, LLM_memory_cache

    # check who we are currently talking too - if someone new is talking to us, fetch their memories
    # if it's a different user, cache the current history to file the swap out the memories
    if user_name != LLM_current_chatter:
        print(f"⚠️ SWITCHING CONVERSER FROM {LLM_current_chatter} > {user_name}")

        # search through memory cache for user
        # print(f"{LLM_memory_cache}")

        user_convo_history = []

        # Loop through and check for the user
        found_user_cache = False
        if str(user_name) in LLM_memory_cache:
            json_string = LLM_memory_cache[str(user_name)]
            data = json.loads(json_string)
            print(f"✅ FOUND USER CACHE FOR {user_name}")
            found_user_cache = True
            user_convo_history = data

        # if we don't already have the user in our memory cache, we need to get it
        if not found_user_cache:
            user_convo_history = await memory_fetch_user_conversations(client, user_name)

        # set short term memories to the memories we have fetched
        LLM_Current_Conversation_History = user_convo_history

    # set current chatter to who we are talking too now
    LLM_current_chatter = user_name

    # print(f"{LLM_Current_Conversation_History}")

    flukebot_context = f"""
You are currently talking to {user_name}, their name is {user_name},
if the person you are chatting too asks what their name is, you know their name as {user_name}.
if {user_name} mentions flukebot in any context, its safe to assume they are talking about you,
and not some other entity called flukebot.
"""

    # continue as normal
    response = chat(
        model='flukebot',
        messages=[{
            'role': 'system',
            'content': flukebot_rules + flukebot_context
        }] + LLM_Current_Conversation_History + [{'role': 'user', 'name': user_name, 'content': user_input}],
    )

    # Add the response to the messages to maintain the history
    chat_new_history = [
        {'role': 'user', 'name': user_name, 'content': user_input},
        {'role': 'assistant', 'content': response.message.content},
    ]
    LLM_Current_Conversation_History += chat_new_history

    # Debug Console Output
    print("\n===================================\n")

    print(f"{user_name} REPLY:\n" + user_input + '\n')
    print("RESPONSE:\n" + response.message.content)

    print("\n===================================\n")

    # add chat to memory cache
    json_string = json.dumps(LLM_Current_Conversation_History)
    LLM_memory_cache[user_name] = json_string
    # print(f"{LLM_memory_cache}")

    # Append the url reference of the memory to file
    convo_write_memories(user_name, chat_new_history, message_channel_reference)

    # return the message to main script
    return response.message.content
