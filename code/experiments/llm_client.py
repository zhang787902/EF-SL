"""
LLM Client with Baidu Qianfan Anthropic API Support
兼容百度千帆 Claude API (Anthropic 协议)
"""
import os
import requests
import json
from typing import Optional, List, Dict
import time


class QianfanLLMClient:
    """LLM Client using Baidu Qianfan Anthropic API"""

    def __init__(self, api_key: str = None, base_url: str = None, model: str = "claude-opus-4-6", temperature: float = 0.3):
        """
        Initialize LLM Client (OpenAI兼容模式)

        Args:
            api_key: API Key
            base_url: Base URL for API (默认: http://localhost:3000/v1)
            model: Model name (默认: claude-sonnet-4-6)
            temperature: Temperature for generation
        """
        self.api_key = api_key or os.getenv("LLM_API_KEY")
        self.base_url = base_url or "https://hub.codesuc.top/v1"
        self.model = model
        self.temperature = temperature

        # 检测 API 类型：默认使用 OpenAI 格式
        self.api_type = "openai"  # 默认 OpenAI 兼容格式
        if "anthropic" in self.base_url or "qianfan" in self.base_url:
            self.api_type = "anthropic"

        # 移除末尾的 /messages (会自动添加)
        self.base_url = self.base_url.rstrip('/').replace('/messages', '')

        self.session = requests.Session()

    def _extract_sql(self, text: str) -> str:
        """Extract SQL from markdown code blocks or plain text"""
        import re

        # Try to extract SQL from markdown code blocks
        # Pattern: ```sql ... ``` or ``` ... ```
        patterns = [
            r'```sql\s*\n(.*?)\n```',  # ```sql ... ```
            r'```SQL\s*\n(.*?)\n```',  # ```SQL ... ```
            r'```\s*\n(.*?)\n```',      # ``` ... ```
            r'```sql\s*(.*?)\s*```',     # ```sql ... ``` (single line)
            r'```\s*(.*?)\s*```',         # ``` ... ``` (single line)
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                # Return the first match, cleaned up
                sql = matches[0].strip()
                # Remove any trailing semicolons for consistent comparison
                sql = sql.rstrip(';')
                return sql

        # If no code block found, return the text as-is (cleaned)
        text = text.strip()
        text = text.rstrip(';')
        return text

    def _get_headers(self) -> Dict:
        """Get request headers"""
        headers = {
            "Content-Type": "application/json"
        }
        # 使用 Bearer Token 认证格式
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def generate(self, prompt: str, temperature: Optional[float] = None, max_retries: int = 3) -> str:
        """
        Generate text using Qianfan Anthropic API or OpenAI API

        Args:
            prompt: Input prompt
            temperature: Override temperature
            max_retries: Maximum retry attempts

        Returns:
            Generated text
        """
        temp = temperature if temperature is not None else self.temperature

        if self.api_type == "openai":
            # OpenAI 格式
            url = f"{self.base_url}/chat/completions"
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a SQL expert. Generate SQL queries based on the given question and schema."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temp,
                "max_tokens": 512
            }
        else:
            # Anthropic 格式 (百度千帆)
            url = f"{self.base_url}/messages"
            payload = {
                "model": self.model,
                "max_tokens": 512,
                "temperature": temp,
                "system": "You are a SQL expert. Generate SQL queries based on the given question and schema.",
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }

        for attempt in range(max_retries):
            try:
                response = self.session.post(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=60
                )

                if response.status_code == 200:
                    result = response.json()
                    content = ""

                    # 尝试多种响应格式
                    # 方式1: OpenAI 格式
                    if "choices" in result and len(result["choices"]) > 0:
                        content = result["choices"][0]["message"]["content"].strip()
                    # 方式2: Anthropic 格式
                    elif "content" in result and len(result["content"]) > 0:
                        content = result["content"][0]["text"].strip()
                    # 方式3: 其他可能格式
                    elif "message" in result and "content" in result["message"]:
                        content = result["message"]["content"].strip()
                    elif "response" in result:
                        content = result["response"].strip()
                    elif "output" in result:
                        content = result["output"].strip()
                    elif "text" in result:
                        content = result["text"].strip()
                    else:
                        print(f"Unexpected response format. Keys: {list(result.keys())}")
                        print(f"Response preview: {str(result)[:500]}")
                        return ""

                    # 提取 SQL（处理 markdown 代码块）
                    return self._extract_sql(content)
                else:
                    print(f"API Error (attempt {attempt + 1}/{max_retries}): {response.status_code} - {response.text}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)  # Exponential backoff
                    else:
                        return ""

            except Exception as e:
                print(f"Request Error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return ""

        return ""

    def generate_batch(self, prompts: List[str], temperature: Optional[float] = None) -> List[str]:
        """Generate text for multiple prompts"""
        results = []
        for prompt in prompts:
            result = self.generate(prompt, temperature)
            results.append(result)
            time.sleep(0.5)  # Rate limiting
        return results


class MockLLMClient:
    """Mock LLM client for testing without API"""

    def __init__(self, model: str = "mock", temperature: float = 0.3):
        self.model = model
        self.temperature = temperature

    def generate(self, prompt: str, temperature: Optional[float] = None) -> str:
        """Mock generation - returns simple SQL"""
        if "Question:" in prompt:
            question = prompt.split("Question:")[-1].split("\n")[0].strip()
        else:
            question = ""

        if "salary" in question.lower():
            return "SELECT name FROM instructor WHERE salary > 50000"
        elif "department" in question.lower():
            return "SELECT DISTINCT dept_name FROM instructor"
        elif "average" in question.lower():
            return "SELECT AVG(salary) FROM instructor"
        elif "count" in question.lower():
            return "SELECT COUNT(*) FROM instructor"
        else:
            return "SELECT * FROM instructor LIMIT 10"

    def generate_batch(self, prompts: List[str], temperature: Optional[float] = None) -> List[str]:
        """Mock batch generation"""
        return [self.generate(p, temperature) for p in prompts]


def create_llm_client(use_api: bool = True, api_key: str = None) -> QianfanLLMClient:
    """Factory function to create LLM client"""
    if use_api:
        return QianfanLLMClient(api_key=api_key)
    else:
        return MockLLMClient()


# Test the client
if __name__ == "__main__":
    # Test with mock client
    print("Testing Mock LLM Client:")
    mock = MockLLMClient()
    test_prompt = "Find instructors with salary greater than 50000"
    result = mock.generate(test_prompt)
    print(f"Prompt: {test_prompt}")
    print(f"Result: {result}")

    # Test with real API (if key is set)
    api_key = os.getenv("QIANFAN_API_KEY")
    if api_key:
        print("\nTesting Qianfan Anthropic LLM Client:")
        client = QianfanLLMClient(api_key=api_key)
        result = client.generate(test_prompt)
        print(f"Result: {result}")
    else:
        print("\nQIANFAN_API_KEY not set, skipping API test")
