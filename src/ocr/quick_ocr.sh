#!/bin/bash

# 快速OCR处理脚本
# 用于快速测试单个目录的OCR处理

# 配置
OUTPUT_BASE_DIR="/Volumes/ext/SatExams/data/output"
SCRIPT_DIR="/Volumes/ext/SatExams/src/ocr"
MAX_WORKERS=10

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== 快速OCR处理 ===${NC}"

# 检查参数
if [ $# -eq 0 ]; then
    echo "用法: $0 <目录名> [并行度]"
    echo "示例: $0 '2023年6月（第一套）' 5"
    echo "可用的目录:"
    ls -1 "$OUTPUT_BASE_DIR" | grep -v "^\.$" | grep -v "^\.\.$"
    exit 1
fi

DIR_NAME="$1"
MAX_WORKERS="${2:-10}"

# 构建完整路径
FULL_PATH="$OUTPUT_BASE_DIR/$DIR_NAME"

echo -e "${BLUE}目标目录: $DIR_NAME${NC}"
echo -e "${BLUE}完整路径: $FULL_PATH${NC}"
echo -e "${BLUE}并行度: $MAX_WORKERS${NC}"

# 检查目录是否存在
if [ ! -d "$FULL_PATH" ]; then
    echo -e "${RED}❌ 目录不存在: $FULL_PATH${NC}"
    exit 1
fi

# 检查是否有PNG文件
PNG_COUNT=$(find "$FULL_PATH" -maxdepth 1 -name "*.png" -not -name "._*" | wc -l)
echo -e "${BLUE}发现 $PNG_COUNT 个PNG文件${NC}"

if [ $PNG_COUNT -eq 0 ]; then
    echo -e "${RED}❌ 目录中没有找到PNG文件${NC}"
    exit 1
fi

# 激活虚拟环境
echo -e "${BLUE}激活虚拟环境...${NC}"
source "$SCRIPT_DIR/../venv/bin/activate"

# 切换到脚本目录
cd "$SCRIPT_DIR"

# 运行OCR处理
echo -e "${BLUE}开始OCR处理...${NC}"
python batch_ocr.py --target-dir "$FULL_PATH" --max-workers $MAX_WORKERS

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ OCR处理完成！${NC}"
else
    echo -e "${RED}❌ OCR处理失败！${NC}"
    exit 1
fi
