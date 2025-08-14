# SAT题型识别工具 - 新JSON格式支持

## 概述

SAT题型识别工具现在支持新的JSON格式，可以处理包含多道题目的文件，并且能够区分题干和选项。

## 新格式特性

### 1. 多题目支持
- 一个JSON文件可以包含多道题目
- 每道题目有独立的ID
- 支持批量分析和存储

### 2. 题干和选项分离
- `content`: 题目内容（题干）
- `options`: 选项字典，键为选项标识（如A、B、C、D），值为选项内容

### 3. 数据库结构升级
- 新增 `questions` 表支持新格式
- 保留 `question_types` 表以兼容旧格式
- 支持按文件路径和题目ID查询

## JSON格式示例

```json
{
  "7": {
    "id": "7",
    "content": "In what is now Washington state, the Tulalip Tribes operate the Hibulb Cultural Center...",
    "options": {
      "A": "It suggests improvements to a particular tribal cultural center.",
      "B": "It encourages tribal citizens to attend their local cultural center.",
      "C": "It explains how one tribal cultural center differs from other tribal cultural centers.",
      "D": "It provides a basic description of a particular tribal cultural center."
    }
  },
  "8": {
    "id": "8",
    "content": "The museum of Modern Art (MOMA) in New York City has an exhibition...",
    "options": {
      "A": "It identifies a feature of many video games...",
      "B": "It provides a claim about video games as art...",
      "C": "It describes a misconception about video games...",
      "D": "It presents a consideration that the author thinks..."
    }
  }
}
```

## 使用方法

### 1. 分析单个JSON文件
```bash
python qtype.py example_questions.json --no-ai
```

### 2. 批量分析目录
```bash
python qtype.py /path/to/directory --pattern "*.json" --no-ai
```

### 3. 查询数据库

#### 查看数据库统计
```bash
python qtype.py --db-summary
```

#### 查询新格式数据库中的所有题目
```bash
python qtype.py --db-questions
```

#### 查询特定文件的题目
```bash
python qtype.py --db-file example_questions.json
```

#### 查询旧格式数据库（兼容）
```bash
python qtype.py --db-query
python qtype.py --db-path some_file.png
```

## 数据库结构

### 新表：questions
```sql
CREATE TABLE questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL,
    question_id TEXT NOT NULL,
    question_type TEXT NOT NULL,
    content TEXT NOT NULL,
    options TEXT,
    confidence REAL DEFAULT 0.0,
    add_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(file_path, question_id)
);
```

### 旧表：question_types（兼容）
```sql
CREATE TABLE question_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    png_path TEXT NOT NULL,
    question_type TEXT NOT NULL,
    txt_content TEXT,
    add_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 功能特性

### 1. 自动格式检测
- 自动识别JSON格式文件
- 支持单题目和多题目文件
- 向后兼容旧格式

### 2. 智能题型识别
- 使用AI分析（需要API密钥）
- 规则分析作为备选方案
- 支持所有SAT题型

### 3. 数据管理
- 自动去重（基于文件路径和题目ID）
- 支持更新现有记录
- 完整的查询和统计功能

## 题型分类

### Reading题型
- `reading-evidence`: 阅读证据题
- `reading-words-in-context`: 阅读词汇题
- `reading-command-of-evidence`: 阅读理解题

### Writing题型
- `writing-lang-expression-of-ideas`: 写作表达题
- `writing-lang-grammar`: 写作语法题
- `writing-lang-command-of-evidence`: 写作证据题
- `writing-lang-words-in-context`: 写作词汇题

### Math题型
- `math-heart-of-algebra`: 代数核心题
- `math-problem-solving-data-analysis`: 数据分析题
- `math-passport-to-advanced-math`: 高等数学题
- `math-additional-topics`: 附加数学题

### Essay题型
- `essay-analysis`: 作文分析题

## 测试

运行测试脚本验证功能：
```bash
python test_new_format.py
```

## 注意事项

1. **API密钥**: 使用AI分析需要设置 `OPENAI_API_KEY` 或 `OPENROUTER_API_KEY` 环境变量
2. **文件编码**: JSON文件应使用UTF-8编码
3. **数据库路径**: 数据库文件位于 `/Volumes/ext/SatExams/data/types.db`
4. **兼容性**: 新格式完全向后兼容，不会影响现有数据

## 更新日志

- **v2.0**: 支持新的JSON格式，多题目文件，题干选项分离
- **v1.0**: 基础题型识别功能
