# SAT考试处理工具

这是一个用于处理SAT考试PDF文件的完整工具集，包含PDF解析和OCR文本识别功能。

## 项目结构

```
src/
├── requirements.txt          # 所有模块的依赖汇总
├── parser/                   # PDF解析模块
│   ├── requirements.txt      # PDF解析模块依赖
│   ├── pdf_parser.py         # PDF解析器
│   ├── pdf_splitter.py       # PDF分割器
│   ├── batch_splitter.py     # 批量PDF分割
│   ├── example_usage.py      # 使用示例
│   ├── example_splitter.py   # 分割器示例
│   └── README.md             # 解析模块说明
└── ocr/                      # OCR文本识别模块
    ├── requirements.txt      # OCR模块依赖
    ├── ocr.py               # 单个文件OCR处理
    ├── batch_ocr.py         # 批量OCR处理
    ├── test_ocr.py          # OCR测试脚本
    └── README_OCR.md        # OCR模块说明
```

## 模块说明

### PDF Parser 模块 (`parser/`)

**功能**：
- PDF文件扫描和基本信息提取
- 文本内容提取和分析
- SAT考试内容分类（阅读、写作、数学）
- PDF按页分割为图片

**依赖**：
```bash
cd parser
pip install -r requirements.txt
```

**主要文件**：
- `pdf_parser.py` - 主解析器
- `pdf_splitter.py` - PDF分割器
- `batch_splitter.py` - 批量处理

### OCR 模块 (`ocr/`)

**功能**：
- 使用OpenAI GPT-4 Vision API进行OCR识别
- 图片转文本处理
- 批量OCR处理
- 专门针对SAT题目优化

**依赖**：
```bash
cd ocr
pip install -r requirements.txt
```

**主要文件**：
- `ocr.py` - 单个文件OCR处理
- `batch_ocr.py` - 批量OCR处理
- `test_ocr.py` - 测试脚本

## 安装和使用

### 1. 安装所有依赖

```bash
cd src
source venv/bin/activate
pip install -r requirements.txt
```

### 2. PDF处理

```bash
cd parser
# 分析PDF文件
python pdf_parser.py

# 分割PDF为图片
python pdf_splitter.py input.pdf data/output

# 批量分割
python batch_splitter.py
```

### 3. OCR处理

```bash
cd ocr
# 设置API密钥
export OPENAI_API_KEY="your_key"

# 单个文件OCR
python ocr.py 001.png 001.txt

# 批量OCR
python batch_ocr.py --api-key your_key
```

## 工作流程

1. **PDF处理阶段**：
   - 扫描PDF文件
   - 提取文本内容
   - 按页分割为图片

2. **OCR处理阶段**：
   - 对图片进行OCR识别
   - 生成文本文件
   - 保存到对应目录

## 输出结构

```
data/output/
├── 试卷名称1/
│   ├── 001.png
│   ├── 001.txt          # OCR识别的文本
│   ├── 002.png
│   ├── 002.txt
│   └── 原文件.pdf
└── 试卷名称2/
    ├── 001.png
    ├── 001.txt
    └── ...
```

## 注意事项

1. **OCR模块需要OpenAI API密钥**
2. **PDF处理模块可以独立运行**
3. **建议按模块分别安装依赖**
4. **每个模块都有独立的README文档**

## 开发说明

- 每个模块都是独立的，可以单独使用
- 模块间通过文件系统进行数据交换
- 支持断点续传和错误恢复
- 详细的日志和进度显示
