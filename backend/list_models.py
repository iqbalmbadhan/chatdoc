import google.generativeai as genai
import os
import asyncio

async def list_models():
    api_key = "AIzaSyAS0ptiJ-VPt0ua3Fe-Q7Jxw2xn2oNCvgg"
    genai.configure(api_key=api_key)
    try:
        models = genai.list_models()
        print("Available models:")
        for m in models:
            print(f"- {m.name}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(list_models())
