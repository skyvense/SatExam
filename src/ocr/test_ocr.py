#!/usr/bin/env python3
"""
OCR测试脚本
"""

import os
import sys
from pathlib import Path

# 设置你的OpenAI API密钥
OPENAI_API_KEY = "your_openai_api_key_here"  # 请替换为你的实际API密钥

def test_ocr():
    """测试OCR功能"""
    
    # 设置API密钥
    os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
    
    # 测试图片路径
    test_image = "../../data/output/2025.3 北美A卷/001.png"
    output_text = "001.txt"
    
    if not Path(test_image).exists():
        print(f"测试图片不存在: {test_image}")
        return
    
    print("=== OCR测试 ===")
    print(f"测试图片: {test_image}")
    print(f"输出文件: {output_text}")
    print()
    
    # 运行OCR
    try:
        from ocr import OCRProcessor
        
        processor = OCRProcessor()
        success = processor.process_image(
            Path(test_image), 
            Path(output_text), 
            language="English"
        )
        
        if success:
            print("✅ OCR测试成功!")
            
            # 显示结果
            if Path(output_text).exists():
                with open(output_text, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"\n识别结果 (前500字符):")
                print("-" * 50)
                print(content[:500])
                print("-" * 50)
        else:
            print("❌ OCR测试失败!")
            
    except Exception as e:
        print(f"❌ 错误: {str(e)}")

if __name__ == "__main__":
    if OPENAI_API_KEY == "your_openai_api_key_here":
        print("⚠️  请先在脚本中设置你的OpenAI API密钥!")
        print("1. 打开 test_ocr.py 文件")
        print("2. 找到 OPENAI_API_KEY 变量")
        print("3. 将 'your_openai_api_key_here' 替换为你的实际API密钥")
        sys.exit(1)
    
    test_ocr()
