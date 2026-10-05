#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

print("Testing API key...")
try:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        messages=[
            {"role": "user", "content": "Say 'working' in one word."}
        ]
    )
    print("✅ API Key Valid!")
    print(f"Response: {response.content[0].text}")
except Exception as e:
    print(f"❌ Error: {str(e)[:200]}")
