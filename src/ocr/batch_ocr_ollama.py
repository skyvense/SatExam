#!/usr/bin/env python3
"""
批量OCR处理脚本 (Ollama版本)
使用本地Ollama模型处理所有图片文件，将每页转换为文本文件
"""

import os
import sys
import time
import base64
import json
import requests
from pathlib import Path
from typing import List, Tuple, Optional
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


def get_all_image_files(output_dir: str = "/Volumes/ext/SatExams/data/output", target_dir: str = None) -> List[Tuple[Path, Path]]:
    """
    获取所有需要处理的图片文件
    
    Args:
        output_dir: 输出根目录
        target_dir: 指定要处理的子目录（可选），支持绝对路径（以/开头）
    
    Returns:
        图片文件路径和对应输出文本文件路径的列表
    """
    image_files = []
    
    if target_dir and target_dir.startswith('/'):
        # 处理绝对路径
        target_path = Path(target_dir)
        if not target_path.exists():
            print(f"指定目录不存在: {target_path}")
            return []
        
        # 查找PNG文件
        for png_file in target_path.glob("*.png"):
            # 生成对应的文本文件路径
            text_file = target_path / f"{png_file.stem}.txt"
            image_files.append((png_file, text_file))
    else:
        # 处理相对路径（作为output_dir的子目录）
        output_path = Path(output_dir)
        
        if not output_path.exists():
            print(f"输出目录不存在: {output_dir}")
            return []
        
        if target_dir:
            # 处理指定子目录
            target_path = output_path / target_dir
            if not target_path.exists():
                print(f"指定目录不存在: {target_path}")
                return []
            
            # 查找PNG文件
            for png_file in target_path.glob("*.png"):
                # 生成对应的文本文件路径
                text_file = target_path / f"{png_file.stem}.txt"
                image_files.append((png_file, text_file))
        else:
            # 遍历所有子目录
            for subdir in output_path.iterdir():
                if not subdir.is_dir():
                    continue
                    
                # 查找PNG文件
                for png_file in subdir.glob("*.png"):
                    # 生成对应的文本文件路径
                    text_file = subdir / f"{png_file.stem}.txt"
                    image_files.append((png_file, text_file))
    
    return sorted(image_files)


def batch_process_images(model_name: str = "llava", base_url: str = "http://localhost:11434",
                        output_dir: str = "/Volumes/ext/SatExams/data/output", 
                        target_dir: str = None, max_files: int = None, start_from: int = 0) -> None:
    """批量处理图片文件"""
    
    print("=== 批量OCR处理 (Ollama版本) ===")
    print(f"模型: {model_name}")
    print(f"服务地址: {base_url}")
    print(f"输出目录: {output_dir}")
    if target_dir:
        print(f"目标目录: {target_dir}")
    if max_files:
        print(f"最大处理文件数: {max_files}")
    print(f"起始位置: {start_from}")
    print()
    
    # 获取所有图片文件
    image_files = get_all_image_files(output_dir, target_dir)
    total_files = len(image_files)
    
    if total_files == 0:
        print("没有找到需要处理的图片文件")
        return
    
    print(f"找到 {total_files} 个图片文件")
    
    # 确定处理范围
    end_index = total_files
    if max_files:
        end_index = min(start_from + max_files, total_files)
    
    files_to_process = image_files[start_from:end_index]
    print(f"将处理 {len(files_to_process)} 个文件 (从第{start_from+1}个到第{end_index}个)")
    print()
    
    # 创建OCR处理器
    try:
        processor = OllamaOCRProcessor(model_name=model_name, base_url=base_url)
    except Exception as e:
        print(f"❌ 初始化OCR处理器失败: {str(e)}")
        return
    
    # 统计信息
    success_count = 0
    failed_count = 0
    failed_files = []
    
    # 开始处理
    start_time = time.time()
    
    for i, (image_path, text_path) in enumerate(files_to_process, start=1):
        current_index = start_from + i
        
        # 检查是否已经处理过
        if text_path.exists() and text_path.stat().st_size > 0:
            print(f"[{current_index}/{total_files}] 跳过: {image_path.name} (已存在)")
            success_count += 1
            continue
        
        print(f"[{current_index}/{total_files}] 处理: {image_path.name}")
        print(f"  输入路径: {image_path}")
        print(f"  输出路径: {text_path}")
        
        # 处理文件
        try:
            success = processor.process_image(image_path, text_path, language="English")
            
            if success:
                success_count += 1
            else:
                failed_count += 1
                failed_files.append(image_path.name)
                
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")
            failed_count += 1
            failed_files.append(image_path.name)
        
        # 显示进度
        elapsed = time.time() - start_time
        avg_time = elapsed / i
        remaining = avg_time * (len(files_to_process) - i)
        print(f"  进度: {i}/{len(files_to_process)} | 已用时间: {elapsed:.1f}s | 预计剩余: {remaining:.1f}s")
        print()
        
        # 添加延迟避免过载
        time.sleep(0.5)
    
    # 显示最终结果
    total_time = time.time() - start_time
    print("=== 处理完成 ===")
    print(f"总文件数: {total_files}")
    print(f"成功处理: {success_count}")
    print(f"处理失败: {failed_count}")
    print(f"总耗时: {total_time:.1f}秒")
    if len(files_to_process) > 0:
        print(f"平均时间: {total_time/len(files_to_process):.1f}秒/文件")
    
    if failed_files:
        print(f"\n失败的文件:")
        for file in failed_files[:10]:  # 只显示前10个
            print(f"  - {file}")
        if len(failed_files) > 10:
            print(f"  ... 还有 {len(failed_files) - 10} 个文件")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="批量OCR处理图片文件 (Ollama版本)")
    parser.add_argument("--model", "-m", default="llava", 
                       help="Ollama模型名称 (默认: llava)")
    parser.add_argument("--base-url", "-b", default="http://localhost:11434",
                       help="Ollama服务地址 (默认: http://localhost:11434)")
    parser.add_argument("--output-dir", "-o", default="/Volumes/ext/SatExams/data/output", 
                       help="输出目录 (默认: /Volumes/ext/SatExams/data/output)")
    parser.add_argument("--target-dir", "-t", type=str,
                       help="指定要处理的目录，支持绝对路径（以/开头）或相对路径（作为output-dir的子目录）")
    parser.add_argument("--max-files", type=int,
                       help="最大处理文件数")
    parser.add_argument("--start-from", "-s", type=int, default=0,
                       help="起始文件索引 (默认: 0)")
    
    args = parser.parse_args()
    
    batch_process_images(
        model_name=args.model,
        base_url=args.base_url,
        output_dir=args.output_dir,
        target_dir=args.target_dir,
        max_files=args.max_files,
        start_from=args.start_from
    )


if __name__ == "__main__":
    main()
