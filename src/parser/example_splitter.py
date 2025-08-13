#!/usr/bin/env python3
"""
PDF Splitter 使用示例
"""

import subprocess
import sys
from pathlib import Path

def example_split_pdf():
    """示例：分割单个PDF文件"""
    print("=== PDF Splitter 使用示例 ===")
    
    # 示例PDF文件路径
    pdf_path = "../../data/income/SAT真题/SAT25年3月/2025 年3月 SAT/2025.3 北美A卷.pdf"
    output_dir = "../../data/output"
    
    # 检查PDF文件是否存在
    if not Path(pdf_path).exists():
        print(f"PDF文件不存在: {pdf_path}")
        return
    
    print(f"源PDF: {pdf_path}")
    print(f"输出目录: {output_dir}")
    
    # 运行分割命令
    cmd = [
        sys.executable, "pdf_splitter.py",
        pdf_path,
        output_dir,
        "--dpi", "150"
    ]
    
    print(f"\n执行命令: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✅ 分割成功!")
        print(result.stdout)
        
        # 检查输出目录
        output_path = Path(output_dir) / "2025.3 北美A卷"
        if output_path.exists():
            png_files = list(output_path.glob("*.png"))
            pdf_files = list(output_path.glob("*.pdf"))
            print(f"\n输出结果:")
            print(f"  - 图片文件: {len(png_files)} 个")
            print(f"  - PDF文件: {len(pdf_files)} 个")
            print(f"  - 输出目录: {output_path}")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ 分割失败: {e}")
        print(f"错误输出: {e.stderr}")

def show_usage():
    """显示使用方法"""
    print("\n=== 使用方法 ===")
    print("基本用法:")
    print("  python pdf_splitter.py <pdf_path> <output_root> [--dpi <dpi>]")
    print()
    print("参数说明:")
    print("  pdf_path    - PDF文件路径")
    print("  output_root - 输出根目录")
    print("  --dpi       - 渲染DPI (默认: 200)")
    print()
    print("示例:")
    print("  python pdf_splitter.py input.pdf data/output")
    print("  python pdf_splitter.py input.pdf data/output --dpi 300")
    print()
    print("输出结构:")
    print("  data/output/")
    print("  └── {filename}/")
    print("      ├── 001.png")
    print("      ├── 002.png")
    print("      ├── ...")
    print("      └── {filename}.pdf")

if __name__ == "__main__":
    example_split_pdf()
    show_usage()
