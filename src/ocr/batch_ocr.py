#!/usr/bin/env python3
"""
批量OCR处理脚本
处理所有图片文件，将每页转换为文本文件
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Tuple

from ocr import OCRProcessor


def get_all_image_files(output_dir: str = "../../data/output") -> List[Tuple[Path, Path]]:
    """
    获取所有需要处理的图片文件
    
    Returns:
        图片文件路径和对应输出文本文件路径的列表
    """
    image_files = []
    output_path = Path(output_dir)
    
    if not output_path.exists():
        print(f"输出目录不存在: {output_dir}")
        return []
    
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


def batch_process_images(api_key: str = None, output_dir: str = "../../data/output", 
                        max_files: int = None, start_from: int = 0) -> None:
    """批量处理图片文件"""
    
    print("=== 批量OCR处理 ===")
    print(f"输出目录: {output_dir}")
    if max_files:
        print(f"最大处理文件数: {max_files}")
    print(f"起始位置: {start_from}")
    print()
    
    # 获取所有图片文件
    image_files = get_all_image_files(output_dir)
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
        processor = OCRProcessor(api_key=api_key)
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
                print(f"  ✅ 成功: {text_path.name}")
                success_count += 1
            else:
                print(f"  ❌ 失败")
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
        
        # 添加延迟避免API限制
        time.sleep(1)
    
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
    
    parser = argparse.ArgumentParser(description="批量OCR处理图片文件")
    parser.add_argument("--api-key", type=str, help="OpenAI API密钥")
    parser.add_argument("--output-dir", "-o", default="../../data/output", 
                       help="输出目录 (默认: ../../data/output)")
    parser.add_argument("--max-files", "-m", type=int,
                       help="最大处理文件数")
    parser.add_argument("--start-from", "-s", type=int, default=0,
                       help="起始文件索引 (默认: 0)")
    
    args = parser.parse_args()
    
    # 如果没有提供API密钥，尝试从环境变量获取
    api_key = args.api_key or os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ 需要提供API密钥")
        print("请通过以下方式之一提供:")
        print("1. 设置环境变量: export OPENAI_API_KEY='your_key' 或 export OPENROUTER_API_KEY='your_key'")
        print("2. 使用参数: --api-key your_key")
        sys.exit(1)
    
    batch_process_images(
        api_key=api_key,
        output_dir=args.output_dir,
        max_files=args.max_files,
        start_from=args.start_from
    )


if __name__ == "__main__":
    main()
