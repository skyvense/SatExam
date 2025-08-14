#!/bin/bash

# 简单测试脚本
# 测试单个目录的OCR处理

SCRIPT_DIR="/Volumes/ext/SatExams/src/ocr"
TEST_DIR="/Volumes/ext/SatExams/data/output/2023年12月 A"

echo "=== 简单测试 ==="
echo "测试目录: $TEST_DIR"

# 检查目录是否存在
if [ ! -d "$TEST_DIR" ]; then
    echo "❌ 测试目录不存在: $TEST_DIR"
    exit 1
fi

# 检查PNG文件数量
PNG_COUNT=$(find "$TEST_DIR" -maxdepth 1 -name "*.png" -not -name "._*" 2>/dev/null | wc -l)
echo "PNG文件数量: $PNG_COUNT"

if [ $PNG_COUNT -eq 0 ]; then
    echo "❌ 目录中没有PNG文件"
    exit 1
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source "$SCRIPT_DIR/../venv/bin/activate"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 运行OCR处理
echo "运行OCR处理..."
python batch_ocr.py --target-dir "$TEST_DIR" --max-workers 2 --max-files 3

if [ $? -eq 0 ]; then
    echo "✅ 测试成功！"
else
    echo "❌ 测试失败！"
    exit 1
fi
