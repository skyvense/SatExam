# OCR文本识别工具 (Ollama版本)

使用本地Ollama模型进行高质量的OCR识别，将SAT考试图片转换为文本文件。

## 功能特性

- 🖼️ 支持多种图片格式 (PNG, JPG, JPEG, BMP, TIFF, WEBP)
- 🤖 使用本地Ollama模型进行高精度识别
- 📝 专门针对SAT考试题目优化
- 🔄 支持批量处理
- 📊 详细的处理进度和统计信息
- ⚡ 智能跳过已处理的文件
- 💰 完全免费，无需API密钥

## 前置要求

### 1. 安装Ollama
```bash
# macOS
curl -fsSL https://ollama.ai/install.sh | sh

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# 从 https://ollama.ai/download 下载安装包
```

### 2. 下载视觉模型
```bash
# 下载llava模型（推荐）
ollama pull llava

# 或下载其他支持视觉的模型
ollama pull llava:7b
ollama pull llava:13b
ollama pull llava:34b
```

### 3. 启动Ollama服务
```bash
# 启动Ollama服务
ollama serve

# 在另一个终端中测试
ollama list
```

## 安装依赖

```bash
cd src
source venv/bin/activate
pip install requests pillow
```

## 使用方法

### 单个文件处理

```bash
# 基本用法
python ocr_ollama.py 001.png 001.txt

# 指定模型
python ocr_ollama.py --model llava:13b 001.png 001.txt

# 指定Ollama服务地址
python ocr_ollama.py --base-url http://192.168.1.100:11434 001.png 001.txt

# 指定语言
python ocr_ollama.py --language Chinese 001.png 001.txt
```

### 批量处理

```bash
# 处理所有图片文件
python batch_ocr_ollama.py

# 指定模型
python batch_ocr_ollama.py --model llava:13b

# 处理特定目录
python batch_ocr_ollama.py --target-dir "/Volumes/ext/SatExams/data/output/12月7日北美A卷"

# 限制处理文件数量
python batch_ocr_ollama.py --max-files 10

# 从指定位置开始处理
python batch_ocr_ollama.py --start-from 50
```

## 命令行参数

### ocr_ollama.py
- `input` - 输入图片文件路径
- `output` - 输出文本文件路径
- `--model, -m` - Ollama模型名称 (默认: llava)
- `--base-url, -b` - Ollama服务地址 (默认: http://localhost:11434)
- `--language, -l` - 文本语言 (默认: English)

### batch_ocr_ollama.py
- `--model, -m` - Ollama模型名称 (默认: llava)
- `--base-url, -b` - Ollama服务地址 (默认: http://localhost:11434)
- `--output-dir, -o` - 输出目录 (默认: /Volumes/ext/SatExams/data/output)
- `--target-dir, -t` - 指定要处理的目录
- `--max-files` - 最大处理文件数
- `--start-from, -s` - 起始文件索引 (默认: 0)

## 输出结构

处理后的文件结构：
```
data/output/
├── 12月7日北美A卷/
│   ├── 001.png
│   ├── 001.txt          # OCR识别的文本
│   ├── 002.png
│   ├── 002.txt
│   ├── ...
│   └── 12月7日北美A卷.pdf
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

- **处理速度**: 取决于模型大小和硬件配置
  - llava:7b: 约5-10秒/图片
  - llava:13b: 约10-20秒/图片
  - llava:34b: 约20-40秒/图片
- **准确率**: 与OpenAI GPT-4 Vision相当
- **成本**: 完全免费，无需API费用
- **隐私**: 所有处理都在本地进行

## 支持的模型

### 推荐模型
- `llava` - 默认模型，平衡性能和速度
- `llava:7b` - 轻量级，速度快
- `llava:13b` - 中等大小，准确率高
- `llava:34b` - 大型模型，最高准确率

### 其他视觉模型
- `bakllava` - 另一个优秀的视觉模型
- `llava-llama3` - 基于Llama3的版本
- `llava-llama3.2` - 最新版本

## 故障排除

### 连接问题
```bash
# 检查Ollama服务是否运行
curl http://localhost:11434/api/tags

# 重启Ollama服务
ollama serve
```

### 模型问题
```bash
# 查看已安装的模型
ollama list

# 重新下载模型
ollama pull llava

# 删除模型重新下载
ollama rm llava
ollama pull llava
```

### 内存问题
- 如果遇到内存不足，使用较小的模型（如llava:7b）
- 确保有足够的RAM（建议8GB以上）

## 与云端版本对比

| 特性 | Ollama版本 | 云端版本 |
|------|------------|----------|
| 成本 | 免费 | 按使用量收费 |
| 隐私 | 完全本地 | 数据上传到云端 |
| 速度 | 取决于硬件 | 稳定的网络速度 |
| 可用性 | 需要本地部署 | 随时可用 |
| 模型选择 | 有限 | 丰富 |

## 注意事项

1. **硬件要求**: 建议使用GPU加速（CUDA/OpenCL）
2. **内存要求**: 至少8GB RAM，推荐16GB以上
3. **存储空间**: 模型文件较大（2-20GB）
4. **网络**: 首次下载模型需要网络连接
5. **模型更新**: 定期更新模型以获得最佳效果

## 文件说明

- `ocr_ollama.py` - 单个文件OCR处理
- `batch_ocr_ollama.py` - 批量OCR处理
- `README_Ollama.md` - 使用说明
