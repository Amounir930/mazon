import os
import asyncio
import httpx
from dotenv import load_dotenv

async def test_key():
    load_dotenv('C:/Users/Dell/Desktop/learn/amazon/backend/.env')
    api_key = os.getenv('QWEN_API_KEY')
    print(f"Testing key: {api_key[:10]}...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                "https://api.cerebras.ai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama3.1-8b",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 5
                }
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_key())
