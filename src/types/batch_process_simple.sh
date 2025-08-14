#!/bin/bash

# 简洁的批量处理脚本
# 使用方法: ./batch_process_simple.sh [线程数] [最大文件数]

MAX_WORKERS=${1:-5}
MAX_FILES=${2:-""}
OUTPUT_DIR="/Volumes/ext/SatExams/data/output"
SCRIPT_DIR="/Volumes/ext/SatExams/src/types"

# 颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}=== SAT题型分析批量处理 ===${NC}"
echo -e "线程数: ${MAX_WORKERS}, 最大文件数: ${MAX_FILES:-'无限制'}"

# 检查目录
if [ ! -d "$OUTPUT_DIR" ]; then
    echo -e "${RED}错误: 输出目录不存在${NC}"
    exit 1
fi

cd "$SCRIPT_DIR" || exit 1

# 获取有效目录
echo -e "${YELLOW}扫描目录...${NC}"
valid_dirs=()
cd "$OUTPUT_DIR"
for dir in */; do
    if [ -d "$dir" ]; then
        txt_count=$(find "$dir" -name "*.txt" -not -name "*.type.txt" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$txt_count" -gt 0 ]; then
            valid_dirs+=("$OUTPUT_DIR/$dir")
        fi
    fi
done
cd "$SCRIPT_DIR"

echo -e "${GREEN}找到 ${#valid_dirs[@]} 个有效目录${NC}"

# 处理每个目录
for i in "${!valid_dirs[@]}"; do
    dir="${valid_dirs[$i]}"
    dirname=$(basename "$dir")
    
    echo -e "${BLUE}[$((i+1))/${#valid_dirs[@]}] 处理: ${dirname}${NC}"
    
    # 构建命令
    if [ -n "$MAX_FILES" ]; then
        cmd="source ../venv/bin/activate && python qtype.py \"$dir\" --pattern \"*.txt\" --max-workers $MAX_WORKERS --max-files $MAX_FILES"
    else
        cmd="source ../venv/bin/activate && python qtype.py \"$dir\" --pattern \"*.txt\" --max-workers $MAX_WORKERS"
    fi
    
    # 执行（直接执行，不使用timeout）
    if bash -c "$cmd"; then
        echo -e "${GREEN}  ✓ 成功${NC}"
    else
        echo -e "${RED}  ✗ 失败${NC}"
    fi
    
    echo ""
    [ $i -lt $((${#valid_dirs[@]}-1)) ] && sleep 2
done

echo -e "${BLUE}=== 完成 ===${NC}"
source ../venv/bin/activate && python qtype.py --db-summary
