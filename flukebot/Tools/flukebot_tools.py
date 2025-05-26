import ollama
import asyncio
import yfinance as yf
from typing import Dict, Any, Callable


def get_stock_price(symbol: str) -> float:
    ticker = yf.Ticker(symbol)
    return ticker.info.get('regularMarketPrice') or ticker.fast_info.last_price


async def main():
    client = ollama.AsyncClient()

    prompt = 'What is the current stock price of Google?'

    available_functions: Dict[str, Callable] = {
        'get_stock_price': get_stock_price,
    }

    response = await client.chat(
        model='llama3.2',
        messages=[{'role': 'user', 'content': prompt}],
        tools=[get_stock_price]
    )

    if response.message.tool_calls:
        for tool in response.message.tool_calls:
            if function_to_call := available_functions.get(tool.function.name):
                print('Calling function:', tool.function.name)
                print('Arguments:', tool.function.arguments)
                print('Function output:', function_to_call(**tool.function.arguments))
            else:
                print('Function', tool.function.name, 'not found')

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\nGoodbye!')
