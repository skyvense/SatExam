# OCR文本识别工具

使用OpenAI GPT-4 Vision API进行高质量的OCR文本识别，将SAT考试图片转换为文本文件。

## 功能特性

- 🖼️ 支持多种图片格式 (PNG, JPG, JPEG, BMP, TIFF, WEBP)
- 🤖 使用最新的GPT-4 Vision API进行高精度识别
- 📝 专门针对SAT考试题目优化
- 🔄 支持批量处理
- 📊 详细的处理进度和统计信息
- ⚡ 智能跳过已处理的文件

## 安装依赖

```bash
cd src
source venv/bin/activate
pip install -r requirements.txt
```

## 设置API密钥

### 方法1: 环境变量
```bash
export OPENAI_API_KEY="your_openai_api_key_here"
```

### 方法2: 命令行参数
```bash
python ocr.py --api-key "your_key" input.png output.txt
```

## 使用方法

### 单个文件处理

```bash
# 基本用法
python ocr.py 001.png 001.txt

# 指定语言
python ocr.py --language Chinese 001.png 001.txt

# 指定API密钥
python ocr.py --api-key your_key 001.png 001.txt
```

### 批量处理

```bash
# 处理所有图片文件
python batch_ocr.py --api-key your_key

# 限制处理文件数量
python batch_ocr.py --api-key your_key --max-files 10

# 从指定位置开始处理
python batch_ocr.py --api-key your_key --start-from 50

# 指定输出目录
python batch_ocr.py --api-key your_key --output-dir ../data/output
```

### 测试功能

```bash
# 编辑 test_ocr.py 文件，设置你的API密钥
python test_ocr.py
```

## 输出结构

处理后的文件结构：
```
data/output/
├── 2025.3 北美A卷/
│   ├── 001.png
│   ├── 001.txt          # OCR识别的文本
│   ├── 002.png
│   ├── 002.txt
│   ├── ...
│   └── 2025.3 北美A卷.pdf
└── 其他试卷/
    ├── 001.png
    ├── 001.txt
    └── ...
```

## 识别内容

OCR工具会识别以下内容：
- 题目编号和内容
- 选项A、B、C、D
- 图表和表格中的文字
- 数学公式（LaTeX格式）
- 其他可见文本

## 性能说明

- **处理速度**: 约2-5秒/图片（取决于API响应时间）
- **准确率**: GPT-4 Vision API提供业界领先的识别准确率
- **成本**: 每张图片约$0.01-0.03（取决于图片复杂度）

## 注意事项

1. **API限制**: OpenAI API有速率限制，批量处理时会自动添加延迟
2. **图片质量**: 高分辨率图片识别效果更好
3. **网络连接**: 需要稳定的网络连接访问OpenAI API
4. **成本控制**: 建议先处理少量文件测试效果

## 错误处理

- 自动跳过已处理的文件
- 详细的错误日志
- 支持断点续传
- 失败文件列表记录

## 文件说明

- `ocr.py` - 单个文件OCR处理
- `batch_ocr.py` - 批量OCR处理
- `test_ocr.py` - 测试脚本
- `README_OCR.md` - 使用说明
