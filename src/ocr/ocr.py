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
import time # Added for retry mechanism

import openai
from PIL import Image
import requests


class OCRProcessor:
    """OCR处理器"""
    
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化OCR处理器
        
        Args:
            api_key: API密钥，如果为None则从环境变量获取
            base_url: API基础URL，用于OpenRouter等第三方服务
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("需要提供API密钥，请设置OPENAI_API_KEY或OPENROUTER_API_KEY环境变量或通过参数传入")
        
        # 设置API配置
        if base_url:
            self.client = openai.OpenAI(api_key=self.api_key, base_url=base_url)
        else:
            # 检查是否使用OpenRouter
            openrouter_key = os.getenv('OPENROUTER_API_KEY')
            if openrouter_key:
                self.client = openai.OpenAI(
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1"
                )
            else:
                self.client = openai.OpenAI(api_key=self.api_key)
    
    def encode_image_to_base64(self, image_path: Path) -> str:
        """将图片文件编码为base64字符串"""
        try:
            # 检查文件是否存在
            if not image_path.exists():
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
            # 检查文件大小
            file_size = image_path.stat().st_size
            if file_size == 0:
                raise ValueError(f"图片文件为空: {image_path}")
            
            # 检查文件大小是否过大（OpenAI限制为20MB）
            if file_size > 20 * 1024 * 1024:
                raise ValueError(f"图片文件过大 ({file_size / 1024 / 1024:.1f}MB)，超过20MB限制: {image_path}")
            
            # 验证文件格式
            valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
            if image_path.suffix.lower() not in valid_extensions:
                raise ValueError(f"不支持的图片格式: {image_path.suffix}")
            
            # 尝试读取并编码图片
            with open(image_path, 'rb') as image_file:
                # 读取文件内容
                image_data = image_file.read()
                
                # 验证图片数据是否为空
                if not image_data:
                    raise ValueError(f"图片文件内容为空: {image_path}")
                
                # 编码为base64
                base64_string = base64.b64encode(image_data).decode('utf-8')
                
                # 验证编码结果
                if not base64_string:
                    raise ValueError(f"图片编码失败: {image_path}")
                
                return base64_string
                
        except Exception as e:
            raise Exception(f"图片编码失败 ({image_path}): {str(e)}")
    
    def extract_text_from_image(self, image_path: Path, language: str = "English", 
                               max_retries: int = 3, timeout: int = 60, 
                               backoff_factor: float = 2.0) -> str:
        """
        从图片中提取文本
        
        Args:
            image_path: 图片文件路径
            language: 文本语言 (默认: English)
            max_retries: 最大重试次数 (默认: 3)
            timeout: 超时时间（秒）(默认: 60)
            backoff_factor: 退避因子 (默认: 2.0)
            
        Returns:
            提取的文本内容
        """
        last_exception = None
        
        for attempt in range(max_retries + 1):
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

请按照以下内容输出json格式：
- 保持原始格式和换行
- 清晰标注题目编号
- 保持选项的字母标识
- 保留所有标点符号
- 如果是数学公式，请用LaTeX格式表示
- 如果图片中包含多个题目，请将每个题目分开输出，放到json不同的key中
- 示例json格式：{{"id": "题目序号", "content": "题目内容", "options": {{"A":"a1", "B":"b1", "C":"c1", "D":"d1"}}}}
- 请写规范的json格式，不要有任何其他内容

语言：{language}
"""
                
                # 计算当前超时时间（指数退避）
                current_timeout = timeout * (backoff_factor ** attempt)
                
                # 调用Vision API (支持OpenRouter)
                response = self.client.chat.completions.create(
                    #model="anthropic/claude-3-5-sonnet",  # OpenRouter支持的Vision模型
                    model="openai/gpt-5-mini",
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
                    temperature=0.1,  # 低温度确保准确性
                    timeout=current_timeout  # 设置超时时间
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # 判断是否需要重试
                should_retry = False
                if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    should_retry = True
                    print(f"  超时错误 (尝试 {attempt + 1}/{max_retries + 1}): {error_msg}")
                elif "rate limit" in error_msg.lower() or "too many requests" in error_msg.lower():
                    should_retry = True
                    print(f"  速率限制错误 (尝试 {attempt + 1}/{max_retries + 1}): {error_msg}")
                elif "network" in error_msg.lower() or "connection" in error_msg.lower():
                    should_retry = True
                    print(f"  网络错误 (尝试 {attempt + 1}/{max_retries + 1}): {error_msg}")
                elif "server" in error_msg.lower() or "internal" in error_msg.lower():
                    should_retry = True
                    print(f"  服务器错误 (尝试 {attempt + 1}/{max_retries + 1}): {error_msg}")
                else:
                    print(f"  其他错误 (尝试 {attempt + 1}/{max_retries + 1}): {error_msg}")
                
                # 如果还有重试机会，等待后重试
                if should_retry and attempt < max_retries:
                    wait_time = current_timeout * 0.5  # 等待超时时间的一半
                    print(f"  等待 {wait_time:.1f} 秒后重试...")
                    time.sleep(wait_time)
                    continue
                else:
                    break
        
        # 所有重试都失败了
        raise Exception(f"OCR识别失败 (已重试 {max_retries} 次): {str(last_exception)}")
    
    def process_image(self, input_path: Path, output_path: Path, language: str = "English",
                     max_retries: int = 3, timeout: int = 60, backoff_factor: float = 2.0) -> bool:
        """
        处理单个图片文件
        
        Args:
            input_path: 输入图片路径
            output_path: 输出文本文件路径
            language: 文本语言
            max_retries: 最大重试次数 (默认: 3)
            timeout: 超时时间（秒）(默认: 60)
            backoff_factor: 退避因子 (默认: 2.0)
            
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
            print(f"输入路径: {input_path}")
            print(f"输出路径: {output_path}")
            
            # 提取文本（包含重试逻辑）
            text = self.extract_text_from_image(
                input_path, 
                language, 
                max_retries=max_retries,
                timeout=timeout,
                backoff_factor=backoff_factor
            )
            
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
  python ocr.py --max-retries 5 --timeout 120 001.png 001.txt
        """
    )
    
    parser.add_argument("input_image", type=str, help="输入图片文件路径")
    parser.add_argument("output_text", type=str, help="输出文本文件路径")
    parser.add_argument("--api-key", type=str, help="OpenAI API密钥")
    parser.add_argument("--language", type=str, default="English", 
                       help="文本语言 (默认: English)")
    parser.add_argument("--verbose", "-v", action="store_true", 
                       help="显示详细信息")
    
    # 重试相关参数
    parser.add_argument("--max-retries", type=int, default=3,
                       help="最大重试次数 (默认: 3)")
    parser.add_argument("--timeout", type=int, default=60,
                       help="超时时间（秒）(默认: 60)")
    parser.add_argument("--backoff-factor", type=float, default=2.0,
                       help="退避因子 (默认: 2.0)")
    
    args = parser.parse_args()
    
    try:
        # 创建OCR处理器
        processor = OCRProcessor(api_key=args.api_key)
        
        # 处理文件
        input_path = Path(args.input_image)
        output_path = Path(args.output_text)
        
        success = processor.process_image(
            input_path, 
            output_path, 
            args.language,
            max_retries=args.max_retries,
            timeout=args.timeout,
            backoff_factor=args.backoff_factor
        )
        
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
