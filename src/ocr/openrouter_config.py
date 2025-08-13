#!/usr/bin/env python3
"""
OpenRouter配置示例
展示如何使用OpenRouter API进行OCR识别
"""

import os
from pathlib import Path
from ocr import OCRProcessor

def setup_openrouter():
    """设置OpenRouter配置"""
    
    # 方法1: 环境变量设置
    os.environ['OPENROUTER_API_KEY'] = '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'
    
    # 方法2: 直接创建客户端
    processor = OCRProcessor(
        api_key='your_openrouter_api_key_here',
        base_url='https://openrouter.ai/api/v1'
    )
    
    return processor

def test_openrouter_models():
    """测试不同的OpenRouter模型"""
    
    # 可用的Vision模型
    vision_models = [
        "openai/gpt-4-vision-preview",  # GPT-4 Vision
        "anthropic/claude-3-5-sonnet",  # Claude 3.5 Sonnet
        "google/gemini-pro-vision",     # Gemini Pro Vision
    ]
    
    print("OpenRouter支持的Vision模型:")
    for model in vision_models:
        print(f"  - {model}")
    
    return vision_models

def custom_model_ocr(image_path: str, model: str = "openai/gpt-4-vision-preview"):
    """使用指定模型进行OCR"""
    
    processor = setup_openrouter()
    
    # 自定义模型调用
    try:
        # 这里可以修改processor中的模型名称
        # 在ocr.py中的extract_text_from_image方法中修改model参数
        result = processor.process_image(
            Path(image_path),
            Path("output.txt"),
            language="English"
        )
        return result
    except Exception as e:
        print(f"OCR失败: {e}")
        return False

if __name__ == "__main__":
    print("=== OpenRouter配置示例 ===")
    
    # 显示可用模型
    models = test_openrouter_models()
    
    print("\n使用方法:")
    print("1. 设置环境变量: export OPENROUTER_API_KEY='your_key'")
    print("2. 运行OCR: python ocr.py input.png output.txt")
    print("3. 或运行批量处理: python batch_ocr.py")
    
    print("\nOpenRouter优势:")
    print("- 支持多种AI模型")
    print("- 价格更灵活")
    print("- 统一的API接口")
    print("- 更好的可用性")
