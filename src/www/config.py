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
