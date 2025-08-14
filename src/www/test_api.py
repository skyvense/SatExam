#!/usr/bin/env python3
"""
测试OpenRouter API连接
"""

import requests
import json
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL

def test_openrouter_api():
    """测试OpenRouter API连接"""
    print("开始测试OpenRouter API...")
    print(f"API URL: {OPENROUTER_BASE_URL}")
    print(f"模型: {OPENROUTER_MODEL}")
    print(f"API密钥: {OPENROUTER_API_KEY[:10]}...")
    
    headers = {
        'Authorization': f'Bearer {OPENROUTER_API_KEY}',
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://localhost:8080',
        'X-Title': 'SAT Answer Check'
    }
    
    data = {
        'model': OPENROUTER_MODEL,
        'messages': [
            {
                'role': 'user',
                'content': 'Hello, please respond with "API test successful"'
            }
        ],
        'temperature': 0.3,
        'max_tokens': 50
    }
    
    try:
        print("发送测试请求...")
        response = requests.post(
            f'{OPENROUTER_BASE_URL}/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"响应状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text[:500]}...")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API测试成功!")
            print(f"AI响应: {result['choices'][0]['message']['content']}")
        else:
            print("❌ API测试失败!")
            print(f"错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")
        import traceback
        print(f"详细错误: {traceback.format_exc()}")

if __name__ == "__main__":
    test_openrouter_api()
