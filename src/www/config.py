#!/usr/bin/env python3
"""
Web应用配置文件
"""

import os

# OpenRouter API配置
OPENROUTER_API_KEY = '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'
OPENROUTER_MODEL = 'openai/gpt-4o-mini'  # 使用与qtype.py相同的模型
OPENROUTER_BASE_URL = 'https://openrouter.ai/api/v1'

# 数据库配置
DB_PATH = "/Volumes/ext/SatExams/data/types.db"

# 应用配置
DEBUG = True
HOST = '0.0.0.0'
PORT = 8080
