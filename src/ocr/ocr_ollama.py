#!/usr/bin/env python3
"""
OCR文本识别工具 (Ollama版本)
使用本地Ollama模型进行高质量的OCR识别
将图片转换为文本文件

用法:
    python ocr_ollama.py <input_image> <output_text_file>
示例:
    python ocr_ollama.py 001.png 001.txt
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional

import requests
from PIL import Image


class OllamaOCRProcessor:
    """Ollama OCR处理器"""
    
    def __init__(self, model_name: str = "llava", base_url: str = "http://localhost:11434"):
        """
        初始化Ollama OCR处理器
        
        Args:
            model_name: Ollama模型名称 (默认: llava)
            base_url: Ollama服务地址 (默认: http://localhost:11434)
        """
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        
        # 测试连接
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code != 200:
                raise ConnectionError(f"无法连接到Ollama服务: {response.status_code}")
            print(f"✅ 成功连接到Ollama服务: {self.base_url}")
        except Exception as e:
            raise ConnectionError(f"连接Ollama服务失败: {e}")
    
    def encode_image_to_base64(self, image_path: Path) -> str:
        """
        将图片编码为base64字符串
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            base64编码的图片字符串
        """
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def extract_text_from_image(self, image_path: Path, language: str = "English") -> str:
        """
        从图片中提取文本
        
        Args:
            image_path: 图片文件路径
            language: 文本语言 (默认: English)
            
        Returns:
            提取的文本内容
        """
        try:
            # 编码图片
            base64_image = self.encode_image_to_base64(image_path)
            
            # 构建提示词
            prompt = f"""
请仔细识别这张图片中的所有文本内容。这是一张SAT考试题目图片，包含：

1. 题目编号和内容
2. 选项A、B、C、D（如果有）
3. 图表、表格中的文字
4. 任何其他可见的文本

请按照以下格式输出：
- 保持原始格式和换行
- 清晰标注题目编号
- 保持选项的字母标识
- 保留所有标点符号
- 如果是数学公式，请用LaTeX格式表示

语言：{language}

请开始识别：
"""
            
            # 调用Ollama API
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "images": [base64_image],
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9,
                    "num_predict": 2048
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=60
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama API调用失败: {response.status_code} - {response.text}")
            
            result = response.json()
            return result.get("response", "").strip()
            
        except Exception as e:
            raise Exception(f"OCR处理失败: {e}")
    
    def process_image(self, image_path: Path, text_path: Path, language: str = "English") -> bool:
        """
        处理单个图片文件
        
        Args:
            image_path: 输入图片路径
            text_path: 输出文本路径
            language: 文本语言
            
        Returns:
            处理是否成功
        """
        try:
            print(f"正在处理: {image_path.name}")
            print(f"输入路径: {image_path}")
            print(f"输出路径: {text_path}")
            
            # 提取文本
            text_content = self.extract_text_from_image(image_path, language)
            
            # 保存文本文件
            with open(text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            print(f"✅ 成功: {text_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="OCR文本识别工具 (Ollama版本)")
    parser.add_argument("input", type=str, help="输入图片文件路径")
    parser.add_argument("output", type=str, help="输出文本文件路径")
    parser.add_argument("--model", "-m", default="llava", 
                       help="Ollama模型名称 (默认: llava)")
    parser.add_argument("--base-url", "-b", default="http://localhost:11434",
                       help="Ollama服务地址 (默认: http://localhost:11434)")
    parser.add_argument("--language", "-l", default="English",
                       help="文本语言 (默认: English)")
    
    args = parser.parse_args()
    
    # 检查输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 输入文件不存在: {input_path}")
        sys.exit(1)
    
    # 检查输出目录
    output_path = Path(args.output)
    output_dir = output_path.parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建OCR处理器
    try:
        processor = OllamaOCRProcessor(model_name=args.model, base_url=args.base_url)
    except Exception as e:
        print(f"❌ 初始化OCR处理器失败: {e}")
        sys.exit(1)
    
    # 处理图片
    success = processor.process_image(input_path, output_path, args.language)
    
    if success:
        print("🎉 OCR处理完成！")
        sys.exit(0)
    else:
        print("❌ OCR处理失败！")
        sys.exit(1)


if __name__ == "__main__":
    main()
