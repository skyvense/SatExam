#!/bin/bash

# SAT题目重新分类脚本
# 使用新的题型分类和更便宜的AI模型

echo "=========================================="
echo "SAT题目重新分类工具"
echo "使用新的题型分类和更便宜的AI模型"
echo "=========================================="

# 设置环境变量
export PYTHONPATH="/Volumes/ext/SatExams/src:$PYTHONPATH"

# 检查API密钥
if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "错误: 请设置 OPENROUTER_API_KEY 环境变量"
    echo "export OPENROUTER_API_KEY='your_api_key_here'"
    exit 1
fi

echo "使用API密钥: ${OPENROUTER_API_KEY:0:10}..."

# 创建输出目录
mkdir -p /Volumes/ext/SatExams/data/output_reclassified

# 备份原始数据库
echo "备份原始数据库..."
cp /Volumes/ext/SatExams/data/types.db /Volumes/ext/SatExams/data/types.db.backup.$(date +%Y%m%d_%H%M%S)

# 重新分类所有文件
echo "开始重新分类所有SAT题目文件..."

cd /Volumes/ext/SatExams/src/types

# 使用Python脚本重新分类
python3 qtype.py /Volumes/ext/SatExams/data/output \
    --pattern "*.txt" \
    --force-reanalyze \
    --max-workers 3 \
    --batch-size 20 \
    --output "/Volumes/ext/SatExams/data/output_reclassified/question_types_new.json"

echo "=========================================="
echo "重新分类完成！"
echo "=========================================="

# 生成统计报告
echo "生成统计报告..."
python3 qtype.py --db-summary > /Volumes/ext/SatExams/data/output_reclassified/database_summary.txt

echo "结果文件:"
echo "- 分类结果: /Volumes/ext/SatExams/data/output_reclassified/question_types_new.json"
echo "- 数据库摘要: /Volumes/ext/SatExams/data/output_reclassified/database_summary.txt"
echo "- 数据库备份: /Volumes/ext/SatExams/data/types.db.backup.*"

echo "=========================================="
echo "完成！"
echo "=========================================="
