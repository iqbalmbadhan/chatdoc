import httpx
import asyncio
import json

async def test_chat():
    url = "http://localhost:8000/chat"
    payload = {
        "message": "Hello",
        "session_id": "test-session",
        "provider": "gemini",
        "model": "gemini-2.0-flash"
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(url, json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
