"""
API Configuration for Baidu Qianfan Platform
兼容OpenAI接口协议
"""
import os

# Baidu Qianfan API Configuration
# 兼容OpenAI接口协议

API_CONFIG = {
    # API密钥
    'api_key': 'sk-lO28ur9uK0YibWWQnGQlsZWj1Qouw1SjLIKodSbXiZGyEe7b',

    # Base URL (OpenAI兼容接口)
    'base_url': 'https://hub.codesuc.top/v1',

    # 完整调用路径
    'chat_completion_url': 'https://hub.codesuc.top/v1/chat/completions',

    # 模型选择
    'model': 'claude-opus-4-6',  # Claude Opus 4.6

    # 温度参数
    'temperature': 0.3,

    # 最大token数
    'max_tokens': 512,

    # 超时设置
    'timeout': 30,

    # 重试次数
    'max_retries': 3
}


def get_api_config():
    """获取API配置"""
    # 优先从环境变量读取
    api_key = os.getenv('QIANFAN_API_KEY', API_CONFIG['api_key'])
    base_url = os.getenv('QIANFAN_BASE_URL', API_CONFIG['base_url'])

    return {
        'api_key': api_key,
        'base_url': base_url,
        'model': API_CONFIG['model'],
        'temperature': API_CONFIG['temperature'],
        'max_tokens': API_CONFIG['max_tokens'],
        'timeout': API_CONFIG['timeout'],
        'max_retries': API_CONFIG['max_retries']
    }


def setup_environment():
    """设置环境变量"""
    os.environ['QIANFAN_API_KEY'] = API_CONFIG['api_key']
    os.environ['QIANFAN_BASE_URL'] = API_CONFIG['base_url']
    os.environ['OPENAI_API_KEY'] = API_CONFIG['api_key']  # 兼容OpenAI SDK
    os.environ['OPENAI_BASE_URL'] = API_CONFIG['base_url']  # 兼容OpenAI SDK
    print("[OK] API环境变量已设置")
