#!/usr/bin/env python3
"""
PDF Splitter
将单个PDF按页渲染为PNG图片，输出目录结构：
  data/output/{filename_without_ext}/001.png
同时会把源PDF拷贝到该输出目录。

用法：
  python pdf_splitter.py <pdf_path> <output_root>
示例：
  python pdf_splitter.py ../../data/income/SAT真题/SAT25年3月/2025 年3月 SAT/2025.3 北美A卷.pdf ../../data/output
"""

import argparse
import os
import shutil
from pathlib import Path
from typing import Tuple

import pypdfium2 as pdfium
from PIL import Image


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def normalize_filename_to_dirname(pdf_path: Path) -> str:
    # 目录名使用PDF文件名（含中文等），去掉扩展名
    return pdf_path.name.rsplit('.', 1)[0]


def split_pdf_to_images(pdf_path: Path, output_root: Path, dpi: int = 200) -> Tuple[Path, int]:
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    if not pdf_path.is_file():
        raise ValueError(f"Not a file: {pdf_path}")

    # 输出目录: {output_root}/{filename_without_ext}
    dirname = normalize_filename_to_dirname(pdf_path)
    target_dir = output_root / dirname
    ensure_dir(target_dir)

    # 先复制原PDF到输出目录
    target_pdf_path = target_dir / pdf_path.name
    if not target_pdf_path.exists():
        shutil.copy2(pdf_path, target_pdf_path)

    # 渲染
    pdf = pdfium.PdfDocument(str(pdf_path))
    page_count = len(pdf)

    # 逐页输出为 PNG
    for index in range(page_count):
        page = pdf[index]
        bitmap = page.render(scale=dpi/72.0)  # 72dpi 是PDF点的基准
        img = bitmap.to_pil()
        img = img.convert("RGB")
        # 输出文件名: 001.png, 002.png ...
        filename = f"{index+1:03d}.png"
        out_path = target_dir / filename
        img.save(out_path, format="PNG")

    return target_dir, page_count


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Split a single PDF into per-page PNG images")
    parser.add_argument("pdf_path", type=str, help="Path to the source PDF file")
    parser.add_argument("output_root", type=str, help="Root output directory, e.g., data/output")
    parser.add_argument("--dpi", type=int, default=200, help="Render DPI (default: 200)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_path = Path(args.pdf_path).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    ensure_dir(output_root)

    target_dir, pages = split_pdf_to_images(pdf_path, output_root, dpi=args.dpi)
    print(f"Done. Output: {target_dir}  (pages: {pages})")


if __name__ == "__main__":
    main()
