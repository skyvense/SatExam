#!/usr/bin/env python3
"""
批量PDF分割器
循环处理所有PDF文件，将它们按页分割为PNG图片
"""

import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple

def get_all_pdf_files(data_dir: str = "../../data/income/SAT真题") -> List[Path]:
    """获取所有PDF文件路径"""
    pdf_files = []
    for pdf_path in Path(data_dir).rglob("*.pdf"):
        pdf_files.append(pdf_path)
    return sorted(pdf_files)

def split_single_pdf(pdf_path: Path, output_root: Path, dpi: int = 150) -> Tuple[bool, str]:
    """分割单个PDF文件"""
    try:
        cmd = [
            sys.executable, "pdf_splitter.py",
            str(pdf_path),
            str(output_root),
            "--dpi", str(dpi)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, result.stdout.strip()
        
    except subprocess.CalledProcessError as e:
        return False, f"错误: {e.stderr.strip()}"
    except Exception as e:
        return False, f"异常: {str(e)}"

def batch_process_pdfs(output_root: str = "../../data/output", dpi: int = 150, 
                      max_files: int = None, start_from: int = 0) -> None:
    """批量处理PDF文件"""
    
    print("=== 批量PDF分割器 ===")
    print(f"输出目录: {output_root}")
    print(f"DPI设置: {dpi}")
    print(f"起始位置: {start_from}")
    if max_files:
        print(f"最大处理文件数: {max_files}")
    print()
    
    # 获取所有PDF文件
    pdf_files = get_all_pdf_files()
    total_files = len(pdf_files)
    
    print(f"找到 {total_files} 个PDF文件")
    
    # 确定处理范围
    end_index = total_files
    if max_files:
        end_index = min(start_from + max_files, total_files)
    
    files_to_process = pdf_files[start_from:end_index]
    print(f"将处理 {len(files_to_process)} 个文件 (从第{start_from+1}个到第{end_index}个)")
    print()
    
    # 创建输出目录
    output_path = Path(output_root)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 统计信息
    success_count = 0
    failed_count = 0
    failed_files = []
    
    # 开始处理
    start_time = time.time()
    
    for i, pdf_path in enumerate(files_to_process, start=1):
        current_index = start_from + i
        print(f"[{current_index}/{total_files}] 处理: {pdf_path.name}")
        
        # 检查是否已经处理过
        dirname = pdf_path.name.rsplit('.', 1)[0]
        target_dir = output_path / dirname
        if target_dir.exists() and list(target_dir.glob("*.png")):
            print(f"  ⏭️  跳过 (已存在)")
            success_count += 1
            continue
        
        # 处理文件
        success, message = split_single_pdf(pdf_path, output_path, dpi)
        
        if success:
            print(f"  ✅ 成功: {message}")
            success_count += 1
        else:
            print(f"  ❌ 失败: {message}")
            failed_count += 1
            failed_files.append(pdf_path.name)
        
        # 显示进度
        elapsed = time.time() - start_time
        avg_time = elapsed / i
        remaining = avg_time * (len(files_to_process) - i)
        print(f"  进度: {i}/{len(files_to_process)} | 已用时间: {elapsed:.1f}s | 预计剩余: {remaining:.1f}s")
        print()
    
    # 显示最终结果
    total_time = time.time() - start_time
    print("=== 处理完成 ===")
    print(f"总文件数: {total_files}")
    print(f"成功处理: {success_count}")
    print(f"处理失败: {failed_count}")
    print(f"总耗时: {total_time:.1f}秒")
    print(f"平均时间: {total_time/len(files_to_process):.1f}秒/文件")
    
    if failed_files:
        print(f"\n失败的文件:")
        for file in failed_files:
            print(f"  - {file}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="批量处理PDF文件")
    parser.add_argument("--output", "-o", default="../../data/output", 
                       help="输出根目录 (默认: ../../data/output)")
    parser.add_argument("--dpi", "-d", type=int, default=150,
                       help="渲染DPI (默认: 150)")
    parser.add_argument("--max-files", "-m", type=int,
                       help="最大处理文件数")
    parser.add_argument("--start-from", "-s", type=int, default=0,
                       help="起始文件索引 (默认: 0)")
    
    args = parser.parse_args()
    
    batch_process_pdfs(
        output_root=args.output,
        dpi=args.dpi,
        max_files=args.max_files,
        start_from=args.start_from
    )

if __name__ == "__main__":
    main()
