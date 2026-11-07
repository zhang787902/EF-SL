#!/usr/bin/env python3
"""
API 测试脚本 - 用于诊断 API 连接问题
"""
import requests
import json

# 配置
API_KEY = "sk-lO28ur9uK0YibWWQnGQlsZWj1Qouw1SjLIKodSbXiZGyEe7b"
BASE_URL = "https://hub.codesuc.top/v1"
MODEL = "claude-sonnet-4-6"

def test_api(auth_type="bearer"):
    """测试不同的认证方式"""

    url = f"{BASE_URL}/chat/completions"

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a SQL expert."},
            {"role": "user", "content": "Generate SQL: Find instructors with salary > 50000"}
        ],
        "temperature": 0.3,
        "max_tokens": 100
    }

    # 根据认证类型设置不同的 headers
    if auth_type == "bearer":
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
    elif auth_type == "api-key":
        headers = {
            "Content-Type": "application/json",
            "api-key": API_KEY
        }
    elif auth_type == "x-api-key":
        headers = {
            "Content-Type": "application/json",
            "x-api-key": API_KEY
        }
    elif auth_type == "raw":
        headers = {
            "Content-Type": "application/json",
            "Authorization": API_KEY  # 不带 Bearer
        }
    else:
        headers = {"Content-Type": "application/json"}

    print(f"\n{'='*60}")
    print(f"Testing auth type: {auth_type}")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    print(f"{'='*60}")

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )

        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {response.text[:500]}")

        if response.status_code == 200:
            result = response.json()
            if "choices" in result:
                content = result["choices"][0]["message"]["content"]
                print(f"\n✅ Success! Generated SQL: {content[:100]}...")
                return True

    except Exception as e:
        print(f"\n❌ Error: {e}")

    return False


if __name__ == "__main__":
    # 测试不同的认证方式
    auth_types = ["bearer", "api-key", "x-api-key", "raw"]

    for auth_type in auth_types:
        if test_api(auth_type):
            print(f"\n🎉 成功! 使用认证方式: {auth_type}")
            break
    else:
        print("\n⚠️ 所有认证方式都失败了")
        print("\n可能的解决方案:")
        print("1. 确认 API Key 是否正确")
        print("2. 确认 API 服务是否在线")
        print("3. 查看 API 文档确认认证方式")
        print("4. 确认是否有 IP 白名单限制")
