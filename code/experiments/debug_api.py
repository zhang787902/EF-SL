#!/usr/bin/env python3
"""
API 调试脚本 - 查看完整响应
"""
import requests
import json

API_KEY = "sk-lO28ur9uK0YibWWQnGQlsZWj1Qouw1SjLIKodSbXiZGyEe7b"
BASE_URL = "https://hub.codesuc.top/v1"
MODEL = "claude-opus-4-6"

url = f"{BASE_URL}/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "You are a SQL expert. Generate SQL queries based on the given question and schema."},
        {"role": "user", "content": "Generate SQL: Find instructors with salary > 50000"}
    ],
    "temperature": 0.3,
    "max_tokens": 512
}

print("=" * 70)
print("API Debug Test")
print("=" * 70)
print(f"\nURL: {url}")
print(f"\nHeaders: {json.dumps(headers, indent=2)}")
print(f"\nPayload: {json.dumps(payload, indent=2)}")

try:
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    print(f"\nStatus Code: {response.status_code}")
    print(f"\nFull Response:")
    print("=" * 70)

    result = response.json()
    print(json.dumps(result, indent=2, ensure_ascii=False))

    print("\n" + "=" * 70)
    print("Parsing attempts:")
    print("=" * 70)

    # Try different parsing methods
    if "choices" in result:
        print(f"✓ Found 'choices': {result['choices']}")
        if len(result["choices"]) > 0:
            choice = result["choices"][0]
            print(f"✓ First choice: {choice}")
            if "message" in choice:
                print(f"✓ Found 'message': {choice['message']}")
                if "content" in choice["message"]:
                    print(f"✓ Generated SQL: {choice['message']['content']}")
                else:
                    print("✗ No 'content' in message")
            else:
                print("✗ No 'message' in choice")
    else:
        print("✗ No 'choices' in response")

    if "content" in result:
        print(f"✓ Found 'content' (Anthropic format): {result['content']}")

    if "message" in result:
        print(f"✓ Found 'message': {result['message']}")

    if "response" in result:
        print(f"✓ Found 'response': {result['response']}")

    if "output" in result:
        print(f"✓ Found 'output': {result['output']}")

    if "text" in result:
        print(f"✓ Found 'text': {result['text']}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
