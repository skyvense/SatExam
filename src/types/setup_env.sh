#!/bin/bash
# 设置环境变量脚本

# 设置 OpenRouter API 密钥
export OPENROUTER_API_KEY='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'

echo "环境变量已设置:"
echo "OPENROUTER_API_KEY = $OPENROUTER_API_KEY"
echo ""
echo "现在可以运行题型识别工具了:"
echo "python qtype.py example_questions.json"
echo ""
echo "或者激活虚拟环境后运行:"
echo "source ../venv/bin/activate && python qtype.py example_questions.json"
