#!/usr/bin/env python3
"""
Test client for DuckDuckGo AI Proxy
Demonstrates how to use the proxy with OpenAI-compatible requests
"""

import os
import json
import asyncio
import httpx
from typing import AsyncGenerator

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("DUCKDUCKGO_API_KEY", "sk-duckduckgo-default-key-change-me")


async def test_health_check():
    """Test the health check endpoint."""
    print("\n=== Testing Health Check ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")


async def test_list_models():
    """Test the models listing endpoint."""
    print("\n=== Testing List Models ===")
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/v1/models",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Available models: {len(data['data'])} models")
        for model in data["data"]:
            print(f"  - {model['id']}")


async def test_chat_non_streaming():
    """Test non-streaming chat completion."""
    print("\n=== Testing Non-Streaming Chat ===")
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": "What is the capital of France? Answer in one sentence.",
            }
        ],
        "stream": False,
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{API_BASE_URL}/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"},
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Model: {data['model']}")
            print(f"Response: {data['choices'][0]['message']['content']}")
            if "usage" in data:
                print(f"Tokens used: {data['usage']['total_tokens']}")
        else:
            print(f"Error: {response.text}")


async def test_chat_streaming():
    """Test streaming chat completion."""
    print("\n=== Testing Streaming Chat ===")
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": "Tell me a short joke.",
            }
        ],
        "stream": True,
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{API_BASE_URL}/v1/chat/completions",
            json=payload,
            headers={"Authorization": f"Bearer {API_KEY}"},
        ) as response:
            print(f"Status: {response.status_code}")
            if response.status_code == 200:
                print("Streaming response:")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            print("\n[Stream completed]")
                            break
                        try:
                            data = json.loads(data_str)
                            if "choices" in data and data["choices"]:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    print(content, end="", flush=True)
                        except json.JSONDecodeError:
                            pass
            else:
                print(f"Error: {response.text}")


async def test_different_models():
    """Test different available models."""
    print("\n=== Testing Different Models ===")
    
    models_to_test = ["gpt-4o-mini", "claude-3-5-haiku", "llama-4-scout"]
    
    for model in models_to_test:
        print(f"\nTesting model: {model}")
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": "Say 'Hello' in one word.",
                }
            ],
            "stream": False,
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{API_BASE_URL}/v1/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {API_KEY}"},
                )
                if response.status_code == 200:
                    data = response.json()
                    print(f"  Response: {data['choices'][0]['message']['content'][:100]}")
                else:
                    print(f"  Error: {response.status_code}")
        except Exception as e:
            print(f"  Exception: {e}")


async def main():
    """Run all tests."""
    print("DuckDuckGo AI Proxy - Test Client")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"API Key: {API_KEY[:20]}...")
    
    try:
        await test_health_check()
        await test_list_models()
        await test_chat_non_streaming()
        await test_chat_streaming()
        await test_different_models()
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
