#!/bin/bash

# 批量处理output目录下的所有子目录
# 使用方法: ./batch_process_all.sh [线程数] [最大文件数]

# 配置参数
MAX_WORKERS=${1:-5}  # 默认5个线程
MAX_FILES=${2:-""}   # 默认不限制文件数
OUTPUT_DIR="/Volumes/ext/SatExams/data/output"
SCRIPT_DIR="/Volumes/ext/SatExams/src/types"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== SAT题型分析批量处理脚本 ===${NC}"
echo -e "输出目录: ${OUTPUT_DIR}"
echo -e "线程数: ${MAX_WORKERS}"
echo -e "最大文件数: ${MAX_FILES:-'无限制'}"
echo ""

# 检查输出目录是否存在
if [ ! -d "$OUTPUT_DIR" ]; then
    echo -e "${RED}错误: 输出目录不存在: $OUTPUT_DIR${NC}"
    exit 1
fi

# 切换到脚本目录
cd "$SCRIPT_DIR" || {
    echo -e "${RED}错误: 无法切换到脚本目录: $SCRIPT_DIR${NC}"
    exit 1
}

# 获取所有子目录
echo -e "${YELLOW}扫描目录中...${NC}"
valid_dirs=()

# 使用ls获取子目录列表
cd "$OUTPUT_DIR"
for dir in */; do
    if [ -d "$dir" ]; then
        dir_path="$OUTPUT_DIR/$dir"
        # 检查目录中是否有txt文件
        txt_count=$(find "$dir_path" -name "*.txt" -not -name "*.type.txt" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$txt_count" -gt 0 ]; then
            valid_dirs+=("$dir_path")
        fi
    fi
done

cd "$SCRIPT_DIR"

if [ ${#valid_dirs[@]} -eq 0 ]; then
    echo -e "${YELLOW}警告: 在 $OUTPUT_DIR 中没有找到包含txt文件的子目录${NC}"
    exit 0
fi

echo -e "${GREEN}找到 ${#valid_dirs[@]} 个有效目录:${NC}"
for dir in "${valid_dirs[@]}"; do
    dirname=$(basename "$dir")
    txt_count=$(find "$dir" -name "*.txt" -not -name "*.type.txt" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "  ${dirname} (${txt_count} 个txt文件)"
done
echo ""

# 统计信息
total_processed=0
total_success=0
total_failed=0

# 处理每个子目录
for i in "${!valid_dirs[@]}"; do
    dir="${valid_dirs[$i]}"
    dirname=$(basename "$dir")
    
    echo -e "${BLUE}[$((i+1))/${#valid_dirs[@]}] 处理目录: ${dirname}${NC}"
    echo -e "路径: $dir"
    
    # 检查是否有txt文件
    txt_files=$(find "$dir" -name "*.txt" -not -name "*.type.txt" 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}  找到 ${txt_files} 个txt文件${NC}"
    
    # 构建命令
    if [ -n "$MAX_FILES" ]; then
        cmd="source ../venv/bin/activate && python qtype.py \"$dir\" --pattern \"*.txt\" --max-workers $MAX_WORKERS --max-files $MAX_FILES"
    else
        cmd="source ../venv/bin/activate && python qtype.py \"$dir\" --pattern \"*.txt\" --max-workers $MAX_WORKERS"
    fi
    
    echo -e "${YELLOW}  执行命令: $cmd${NC}"
    echo ""
    
    # 执行命令
    start_time=$(date +%s)
    if timeout 300 bash -c "$cmd"; then
        end_time=$(date +%s)
        duration=$((end_time - start_time))
        echo -e "${GREEN}  ✓ 目录 ${dirname} 处理成功 (耗时: ${duration}秒)${NC}"
        total_success=$((total_success + 1))
    else
        exit_code=$?
        if [ $exit_code -eq 124 ]; then
            echo -e "${RED}  ✗ 目录 ${dirname} 处理超时 (5分钟)${NC}"
        else
            echo -e "${RED}  ✗ 目录 ${dirname} 处理失败 (退出码: $exit_code)${NC}"
        fi
        total_failed=$((total_failed + 1))
    fi
    
    total_processed=$((total_processed + 1))
    echo ""
    echo -e "${BLUE}--- 进度: $((i+1))/${#valid_dirs[@]} ---${NC}"
    echo ""
    
    # 如果不是最后一个目录，暂停一下
    if [ $i -lt $((${#valid_dirs[@]}-1)) ]; then
        echo -e "${YELLOW}暂停3秒后继续下一个目录...${NC}"
        sleep 3
        echo ""
    fi
done

# 显示最终统计
echo -e "${BLUE}=== 处理完成 ===${NC}"
echo -e "总目录数: ${#valid_dirs[@]}"
echo -e "成功处理: ${total_success}"
echo -e "处理失败: ${total_failed}"
echo -e "跳过目录: $((total_processed - total_success - total_failed))"

# 显示数据库统计
echo ""
echo -e "${BLUE}=== 数据库统计 ===${NC}"
cd "$SCRIPT_DIR"
source ../venv/bin/activate
python qtype.py --db-summary

echo ""
echo -e "${GREEN}批量处理完成！${NC}"
