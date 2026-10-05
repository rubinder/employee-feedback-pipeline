#!/usr/bin/env python3
import os
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

print("Checking available models...")
models_to_try = [
    "claude-haiku-4-5-20251001",
    "claude-opus-4-1",
    "claude-sonnet-4-20250514",
    "claude-3-5-sonnet-20241022",
    "claude-3-sonnet-20240229",
    "claude-3-opus-20240229",
    "claude-3-haiku-20240307",
    "claude-opus",
    "claude-sonnet",
    "claude-haiku",
]

for model in models_to_try:
    try:
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "hi"}]
        )
        print(f"✅ {model} - WORKS")
        break
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg and "not_found" in error_msg:
            print(f"❌ {model} - Not available")
        else:
            print(f"⚠️  {model} - {error_msg[:60]}")
