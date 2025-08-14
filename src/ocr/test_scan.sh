#!/bin/bash

# 测试目录扫描脚本
# 验证是否正确处理包含空格的目录名

OUTPUT_BASE_DIR="/Volumes/ext/SatExams/data/output"

echo "=== 测试目录扫描 ==="
echo "输出目录: $OUTPUT_BASE_DIR"
echo

echo "1. 使用find命令列出所有目录:"
find "$OUTPUT_BASE_DIR" -type d | sort

echo
echo "2. 使用find命令列出包含PNG文件的目录:"
find "$OUTPUT_BASE_DIR" -type d | while read -r dir; do
    png_count=$(find "$dir" -maxdepth 1 -name "*.png" -not -name "._*" 2>/dev/null | wc -l)
    if [ $png_count -gt 0 ]; then
        echo "  \"$(basename "$dir")\" ($png_count PNG files)"
    fi
done

echo
echo "3. 测试目录名包含空格的情况:"
find "$OUTPUT_BASE_DIR" -type d | while read -r dir; do
    dir_name=$(basename "$dir")
    if [[ "$dir_name" == *" "* ]]; then
        echo "  发现包含空格的目录: \"$dir_name\""
        png_count=$(find "$dir" -maxdepth 1 -name "*.png" -not -name "._*" 2>/dev/null | wc -l)
        echo "    PNG文件数量: $png_count"
    fi
done
