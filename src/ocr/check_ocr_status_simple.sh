#!/bin/bash

# 简单OCR状态检查脚本
# 统计有多少PNG文件有对应的TXT文件

OUTPUT_BASE_DIR="/Volumes/ext/SatExams/data/output"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== OCR状态检查 ===${NC}"
echo "检查目录: $OUTPUT_BASE_DIR"
echo

# 创建临时文件来存储统计结果
temp_file=$(mktemp)

# 遍历所有子目录并统计
find "$OUTPUT_BASE_DIR" -type d | while read -r dir; do
    # 跳过根目录
    if [ "$dir" = "$OUTPUT_BASE_DIR" ]; then
        continue
    fi
    
    dir_name=$(basename "$dir")
    
    # 统计PNG文件（排除系统文件）
    png_count=$(find "$dir" -maxdepth 1 -name "*.png" -not -name "._*" 2>/dev/null | wc -l)
    
    # 统计TXT文件（排除.type.txt文件）
    txt_count=$(find "$dir" -maxdepth 1 -name "*.txt" -not -name "*.type.txt" 2>/dev/null | wc -l)
    
    if [ $png_count -gt 0 ]; then
        # 计算完成率
        if [ $png_count -eq 0 ]; then
            completion_rate="0%"
        else
            completion_rate=$((txt_count * 100 / png_count))"%"
        fi
        
        # 判断状态
        if [ $txt_count -eq $png_count ] && [ $png_count -gt 0 ]; then
            status="✅ 完成"
        elif [ $txt_count -gt 0 ]; then
            status="⚠️  部分完成"
        else
            status="❌ 未开始"
        fi
        
        printf "%-40s | %6d | %6d | %6s | %s\n" "$dir_name" $png_count $txt_count "$completion_rate" "$status"
        
        # 保存到临时文件
        echo "$png_count $txt_count" >> "$temp_file"
    fi
done

echo
echo -e "${BLUE}=== 总体统计 ===${NC}"

# 计算总数
total_png=0
total_txt=0
total_dirs=0

if [ -f "$temp_file" ]; then
    while read -r line; do
        png_count=$(echo "$line" | cut -d' ' -f1)
        txt_count=$(echo "$line" | cut -d' ' -f2)
        total_png=$((total_png + png_count))
        total_txt=$((total_txt + txt_count))
        total_dirs=$((total_dirs + 1))
    done < "$temp_file"
    rm -f "$temp_file"
fi

echo "总目录数: $total_dirs"
echo "总PNG文件数: $total_png"
echo "总TXT文件数: $total_txt"

if [ $total_png -gt 0 ]; then
    completion_rate=$((total_txt * 100 / total_png))
    echo "总体完成率: ${completion_rate}%"
    
    remaining=$((total_png - total_txt))
    echo "剩余待处理: $remaining 个文件"
    
    if [ $completion_rate -eq 100 ]; then
        echo -e "${GREEN}🎉 所有文件都已处理完成！${NC}"
    elif [ $completion_rate -gt 50 ]; then
        echo -e "${YELLOW}📊 处理进度良好${NC}"
    else
        echo -e "${RED}⚠️  还有大量文件待处理${NC}"
    fi
else
    echo "没有找到PNG文件"
fi

echo
echo -e "${BLUE}=== 快速统计 ===${NC}"

# 快速统计
total_png_files=$(find "$OUTPUT_BASE_DIR" -name "*.png" -not -name "._*" | wc -l)
total_txt_files=$(find "$OUTPUT_BASE_DIR" -name "*.txt" -not -name "*.type.txt" | wc -l)

echo "快速统计结果:"
echo "PNG文件总数: $total_png_files"
echo "TXT文件总数: $total_txt_files"

if [ $total_png_files -gt 0 ]; then
    quick_completion=$((total_txt_files * 100 / total_png_files))
    echo "完成率: ${quick_completion}%"
fi

