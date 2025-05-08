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


dictation_rules = ("You are a simple input output machine. \
The user will feed you a chat message. If you feel strongly about the message, \
reply with a single emoji. Otherwise, respond with \"No reaction\". \
You are only allowed to speak with emoji or only \"No reaction\"."
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
        # print(f"=========\n{content}\n{output}\n=========")
        output = "no reaction"
    return output


def gather_server_emotes(client, bot_server_id):
    guild = client.get_guild(int(bot_server_id))
    if guild is not None:
        for emote in guild.emojis:
            return
            # print(f"{emoji.name}: {emoji.id}")
