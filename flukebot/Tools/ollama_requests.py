import ollama
import requests
import asyncio
from typing import Dict, Any, Callable


async def main():
    client = ollama.AsyncClient()

    prompt = 'get the page for https://forum.gamemaker.io/index.php?members/evanski.28930/'

    available_functions: Dict[str, Callable] = {
        'request': requests.request
    }

    response = await client.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        tools=[requests.request]
    )

    print(response.message.content)
    if response.message.content == '':
        print('nothing')

    for tool in response.message.tool_calls or []:
        function_to_call = available_functions.get(tool.function.name)
        if function_to_call == requests.request:
            resp = function_to_call(
                method=tool.function.arguments.get('method'),
                url=tool.function.arguments.get('url'),
            )
            print(resp.text)
        else:
            print('Function not found:', tool.function.name)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nGoodbye!')
