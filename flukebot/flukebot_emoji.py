import emoji
from ollama import Client, chat, ChatResponse, AsyncClient


def is_emoji(text):
    """
    Checks if a string is an emoji.

    Args:
    text: The string to check.

    Returns:
    True if the string is an emoji, False otherwise.
    """
    return text in emoji.EMOJI_DATA


dictation_rules = ("You are Flukebot, a discord bot. You are roleplaying in a Discord server. \
The user will feed you a chat message. If you feel strongly about the message, \
reply with a single emoji. Otherwise, respond with \"No reaction\". If the chat message is explicit, \
inappropriate or in anyway against your guidelines, again just respond with  \"No reaction\"."
                   )


async def llm_emoji_react_to_message(content):
    client = AsyncClient()
    response = await client.chat(
        model='llama3.2',
        messages=[
            {"role": "system", "content": dictation_rules},
            {"role": "user", "content": content}
        ],
        options={'temperature': 0},  # Make responses more deterministic
    )

    output = response.message.content
    if not is_emoji(output):
        output = "No reaction"
    return output.lower()
