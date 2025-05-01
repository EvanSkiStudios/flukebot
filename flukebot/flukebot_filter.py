import asyncio

from pydantic import BaseModel

from ollama import Client, chat, ChatResponse, AsyncClient


# Define the schema for the response
class MessageDictation(BaseModel):
    directed: bool


class MessageDictationData(BaseModel):
    dictation: list[MessageDictation]


dictation_rules = """
Return True if the following sentence is directly addressing Flukebot (as if speaking to Flukebot), and False if it is not.

Examples:
- "Marco, tell me what you know about Flukebot." → False (this is talking to Marco about Flukebot)
- "Flukebot, how are you feeling?" → True (this is talking to Flukebot directly)
- "flukebot does a box of everything include a copy of itself?" → True (this is talking to Flukebot directly)
Only return "True" or "False"
Now return True or False for the following sentence:
"""


async def LLM_Filter_Message(content):
    client = AsyncClient()
    response = await client.chat(
        model='llama3.2',
        messages=[
            {"role": "user",
             "content": dictation_rules + content}
        ],
        # format=MessageDictationData.model_json_schema(),  # Use Pydantic to generate the schema
        options={'temperature': 0},  # Make responses more deterministic
    )

    # we default to true so the LLM will generate a message even if the filter gives an error
    output_bool = True

    output = response.message.content
    if output.find("False") != -1:
        output_bool = False

    output_list = {"content": response.message.content, "output": output_bool}
    return output_list


# if __name__ == '__main__':
    # message = "marco tell me about flukebot"
    # message = "flukebot does a box of everything include a copy of itself?"
#    message = "flukebot is made using Ollama 3.2"

#    asyncio.run(LLM_Filter_Message(message))
