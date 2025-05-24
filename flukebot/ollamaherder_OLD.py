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


def LLMStartup():
    global llm_current_user_conversation_history, llm_current_user_speaking_too, flukebot_rules, \
        llm_session_memory_cache, current_chatter_character_information

    client = Client()
    response = client.create(
        model='flukebot',
        from_='llama3.2',
        system=flukebot_rules,
        stream=False,
    )
    print(f"# Client: {response.status}")
    return (
        llm_current_user_conversation_history,
        llm_current_user_speaking_too,
        llm_session_memory_cache,
        current_chatter_character_information
    )


async def ollama_response(bot_client, message_author_name, message_content):
    LLMResponse = await LLMConverse(bot_client, message_author_name, message_content)
    response = (LLMResponse
                .replace("'", "\'")
                .replace("evanski_", "Evanski")
                .replace("Evanski_", "Evanski")
                )

    # discord message limit
    # if len(response) > 2000:
    response = split_response(response)
    # else:
    #    response = [response]
    return response


async def LLMConverse(client, user_name, user_input):
    global llm_current_user_conversation_history, llm_current_user_speaking_too, flukebot_rules, llm_session_memory_cache, current_chatter_character_information

    # check who we are currently talking too - if someone new is talking to us, fetch their memories
    # if it's a different user, cache the current history to file the swap out the memories
    if user_name != llm_current_user_speaking_too:
        print(f"⚠️ SWITCHING CONVERSER FROM {llm_current_user_speaking_too} > {user_name}")

        # search through memory cache for user
        # print(f"{LLM_memory_cache}")

        # Loop through and check for the user
        json_string = llm_session_memory_cache.get(user_name)
        if json_string is not None:
            data = json.loads(json_string)
            print(f"✅ FOUND USER CACHE FOR {user_name}")
            user_convo_history = data
        else:
            # if we don't already have the user in our memory cache, we need to get it
            user_convo_history = await memory_fetch_user_conversations(user_name)

        # set short term memories to the memories we have fetched
        # set the information behind the user
        llm_current_user_conversation_history = user_convo_history
        current_chatter_character_information = fetch_chatter_description(user_name)

    # set current chatter to who we are talking too now
    llm_current_user_speaking_too = user_name

    # print(f"{LLM_Current_Conversation_History}")

    flukebot_context = f"""
You are currently talking to {user_name}, their name is {user_name},
if the person you are chatting too asks what their name is, you know their name as {user_name}.
if {user_name} mentions flukebot in any context, its safe to assume they are talking about you,
and not some other entity called flukebot.
"""

    flukebot_system_prompt = flukebot_rules + flukebot_context + current_chatter_character_information

    # continue as normal
    response = chat(
        model='flukebot',
        messages=[
                     {"role": "system", "content": flukebot_system_prompt + "Here is what they have said to you: "}
                 ] + llm_current_user_conversation_history + [
            {"role": "user", "name": user_name, "content": user_input}
                                                        ],
    )

    # Add the response to the messages to maintain the history
    chat_new_history = [
        {"role": "user", "name": user_name, "content": user_input},
        {"role": "assistant", "content": response.message.content},
    ]
    llm_current_user_conversation_history += chat_new_history

    # Debug Console Output
    print("\n===================================\n")
    print(f"{user_name} REPLY:\n" + user_input + '\n')
    print("RESPONSE:\n" + response.message.content)
    print("\n===================================\n")

    # add chat to memory cache
    json_string = json.dumps(llm_current_user_conversation_history)
    llm_session_memory_cache[user_name] = json_string
    # print(f"{LLM_memory_cache}")

    # Append the message to the memory to file
    convo_write_memories(user_name, chat_new_history)

    # return the message to main script
    return response.message.content
