# SAT题型识别模块

用于分析SAT考试题目文本，自动识别题目类型的工具。支持AI分析和规则分析两种模式，具有数据库存储和文件缓存功能。

## 支持的题型

### Reading题型
- **reading-evidence** - 阅读证据题
- **reading-words-in-context** - 阅读词汇题  
- **reading-command-of-evidence** - 阅读理解题

### Writing题型
- **writing-lang-expression-of-ideas** - 写作表达题
- **writing-lang-grammar** - 写作语法题
- **writing-lang-command-of-evidence** - 写作证据题
- **writing-lang-words-in-context** - 写作词汇题

### Math题型
- **math-heart-of-algebra** - 代数核心题
- **math-problem-solving-data-analysis** - 数据分析题
- **math-passport-to-advanced-math** - 高等数学题
- **math-additional-topics** - 附加数学题

### Essay题型
- **essay-analysis** - 作文分析题

## 核心功能

### 1. AI + 规则双重分析
- **AI优先**: 使用OpenAI/OpenRouter API进行高精度题型识别
- **规则回退**: 当AI不可用时，使用关键词和正则表达式进行规则分析
- **置信度评估**: 为每个分析结果提供置信度评分

### 2. 文件缓存系统
- **`.type.txt` 文件**: 每个题目文件对应一个 `.type.txt` 文件存储题型
- **智能缓存**: 下次运行时直接从缓存文件读取，避免重复AI调用
- **强制重新分析**: 支持 `--force-reanalyze` 参数强制重新分析

### 3. 数据库存储
- **SQLite数据库**: 自动创建 `/Volumes/ext/SatExams/data/types.db`
- **完整记录**: 存储PNG路径、题型、文本内容、时间戳
- **查询功能**: 支持查询特定文件或生成统计报告

### 4. 智能文件排序
- **自然排序**: 按文件名中的数字顺序处理文件（001.txt, 002.txt, ...）
- **文件过滤**: 自动排除 `.type.txt` 和系统文件（`._` 开头）

## 使用方法

### 基本用法

```bash
# 分析单个文件
python qtype.py 001.txt

# 批量分析目录
python qtype.py ../../data/output/12月7日北美A卷/

# 限制处理文件数量
python qtype.py ../../data/output/12月7日北美A卷/ --max-files 10
```

### 数据库功能

```bash
# 查询数据库统计报告
python qtype.py --db-summary

# 查询所有记录
python qtype.py --db-query

# 查询特定PNG文件的题型
python qtype.py --db-path "output/12月7日北美A卷/001.png"
```

### 高级选项

```bash
# 强制重新分析（忽略.type.txt缓存）
python qtype.py ../../data/output/12月7日北美A卷/ --force-reanalyze

# 仅使用规则分析（禁用AI）
python qtype.py ../../data/output/12月7日北美A卷/ --no-ai

# 指定API密钥
python qtype.py ../../data/output/12月7日北美A卷/ --api-key "your_key"

# 自定义输出文件
python qtype.py ../../data/output/12月7日北美A卷/ --output results.json
```

## 环境变量设置

```bash
# 设置OpenAI API密钥
export OPENAI_API_KEY="your_openai_key"

# 或设置OpenRouter API密钥
export OPENROUTER_API_KEY="your_openrouter_key"
```

## 输出格式

### JSON结果文件
```json
[
  {
    "filename": "001.txt",
    "filepath": "/path/to/001.txt",
    "question_type": "reading-words-in-context",
    "confidence": 0.95,
    "scores": {
      "reading-words-in-context": 10,
      "reading-evidence": 2,
      "math-heart-of-algebra": 0
    },
    "text_preview": "题目文本预览...",
    "source": "ai_analysis"
  }
]
```

### 数据库表结构
```sql
CREATE TABLE question_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    png_path TEXT NOT NULL,           -- PNG文件路径（相对于data目录）
    question_type TEXT NOT NULL,      -- 识别的题型
    txt_content TEXT,                 -- 完整的文本内容
    add_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 摘要报告
```
SAT题型分析报告
================

总文件数: 50
成功分析: 48
分析失败: 2

题型分布:
  reading-words-in-context: 15 题 (30.0%) - 阅读词汇题
  math-heart-of-algebra: 12 题 (24.0%) - 代数核心题
  writing-lang-grammar: 8 题 (16.0%) - 写作语法题
  ...

=== 数据库统计 ===

数据库题型分析报告
==================

总记录数: 50

题型分布:
  reading-words-in-context: 15 题 (30.0%) - 阅读词汇题
  math-heart-of-algebra: 12 题 (24.0%) - 代数核心题
  ...

最新记录:
  output/12月7日北美A卷/010.png -> writing-lang-expression-of-ideas (2025-08-13 12:24:29)
  output/12月7日北美A卷/009.png -> writing-lang-expression-of-ideas (2025-08-13 12:24:26)
  ...
```

## 识别算法

### AI分析（优先）
1. **OpenAI/OpenRouter API**: 使用Claude-3-5-Sonnet模型
2. **结构化提示**: 提供详细的题型定义和示例
3. **结果验证**: 验证AI返回的题型是否在预定义范围内
4. **置信度**: AI分析置信度为0.95

### 规则分析（回退）
1. **关键词匹配** - 基于预定义的关键词列表
2. **正则表达式匹配** - 使用模式匹配提高准确性
3. **特殊规则** - 针对特定题型的特殊判断逻辑
4. **置信度计算** - 基于匹配分数计算置信度

## 文件结构

```
src/types/
├── qtype.py              # 主程序文件
├── requirements.txt      # 依赖文件
└── README.md            # 说明文档

data/
├── types.db             # SQLite数据库文件
└── output/
    └── 12月7日北美A卷/
        ├── 001.txt      # 题目文本文件
        ├── 001.type.txt # 题型缓存文件
        ├── 001.png      # 原始图片文件
        └── ...
```

## 性能特点

- **智能缓存**: 避免重复AI调用，大幅提升处理速度
- **批量处理**: 支持大量文件的自动化处理
- **断点续传**: 支持中断后继续处理
- **详细日志**: 完整的处理记录和进度显示
- **错误恢复**: 单个文件失败不影响整体处理

## 注意事项

1. **API密钥**: 需要设置OpenAI或OpenRouter API密钥
2. **网络连接**: AI分析需要稳定的网络连接
3. **文件编码**: 文本文件应为UTF-8编码
4. **存储空间**: 数据库和缓存文件会占用一定存储空间
5. **API限制**: 注意API调用频率限制和成本控制
