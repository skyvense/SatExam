# SAT题型识别模块

用于分析SAT考试题目文本，自动识别题目类型的工具。

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

## 使用方法

### 单个文件分析

```bash
python qtype.py 001.txt
```

### 批量分析目录

```bash
python qtype.py ../../data/output/12月7日北美A卷/
```

### 指定输出文件

```bash
python qtype.py ../../data/output/12月7日北美A卷/ --output results.json
```

## 输出格式

### JSON结果文件
```json
[
  {
    "filename": "001.txt",
    "filepath": "/path/to/001.txt",
    "question_type": "reading-words-in-context",
    "confidence": 0.85,
    "scores": {
      "reading-words-in-context": 5,
      "reading-evidence": 2,
      "math-heart-of-algebra": 0
    },
    "text_preview": "题目文本预览..."
  }
]
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
```

## 识别算法

1. **关键词匹配** - 基于预定义的关键词列表
2. **正则表达式匹配** - 使用模式匹配提高准确性
3. **特殊规则** - 针对特定题型的特殊判断逻辑
4. **置信度计算** - 基于匹配分数计算置信度

## 文件说明

- `qtype.py` - 主程序文件
- `requirements.txt` - 依赖文件（仅使用标准库）
- `README.md` - 说明文档
