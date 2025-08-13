#!/usr/bin/env python3
"""
OCR文本识别工具
使用OpenAI GPT-4 Vision API进行高质量的OCR识别
将图片转换为文本文件

用法:
    python ocr.py <input_image> <output_text_file>
示例:
    python ocr.py 001.png 001.txt
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from typing import Optional

import openai
from PIL import Image
import requests


class OCRProcessor:
    """OCR处理器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化OCR处理器
        
        Args:
            api_key: OpenAI API密钥，如果为None则从环境变量获取
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("需要提供OpenAI API密钥，请设置OPENAI_API_KEY环境变量或通过参数传入")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
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
"""
            
            # 调用GPT-4 Vision API
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
                temperature=0.1  # 低温度确保准确性
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"OCR识别失败: {str(e)}")
    
    def process_image(self, input_path: Path, output_path: Path, language: str = "English") -> bool:
        """
        处理单个图片文件
        
        Args:
            input_path: 输入图片路径
            output_path: 输出文本文件路径
            language: 文本语言
            
        Returns:
            是否成功
        """
        try:
            # 检查输入文件
            if not input_path.exists():
                raise FileNotFoundError(f"输入文件不存在: {input_path}")
            
            if not input_path.is_file():
                raise ValueError(f"输入路径不是文件: {input_path}")
            
            # 检查文件格式
            valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
            if input_path.suffix.lower() not in valid_extensions:
                raise ValueError(f"不支持的图片格式: {input_path.suffix}")
            
            print(f"正在处理: {input_path.name}")
            
            # 提取文本
            text = self.extract_text_from_image(input_path, language)
            
            # 确保输出目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入文本文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"✅ 成功: {output_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ 失败: {str(e)}")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="使用OpenAI GPT-4 Vision API进行OCR文本识别",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python ocr.py 001.png 001.txt
  python ocr.py --language Chinese 001.png 001.txt
  python ocr.py --api-key your_key_here 001.png 001.txt
        """
    )
    
    parser.add_argument("input_image", type=str, help="输入图片文件路径")
    parser.add_argument("output_text", type=str, help="输出文本文件路径")
    parser.add_argument("--api-key", type=str, help="OpenAI API密钥")
    parser.add_argument("--language", type=str, default="English", 
                       help="文本语言 (默认: English)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="显示详细信息")
    
    args = parser.parse_args()
    
    try:
        # 创建OCR处理器
        processor = OCRProcessor(api_key=args.api_key)
        
        # 处理文件
        input_path = Path(args.input_image)
        output_path = Path(args.output_text)
        
        success = processor.process_image(input_path, output_path, args.language)
        
        if success:
            print(f"\n🎉 OCR识别完成!")
            print(f"输入: {input_path}")
            print(f"输出: {output_path}")
            
            # 显示文件大小
            if output_path.exists():
                size = output_path.stat().st_size
                print(f"文本文件大小: {size} 字节")
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
