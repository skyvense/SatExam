# OCR脚本使用说明

本目录包含多个OCR处理脚本，用于批量处理SAT考试图片文件。

## 脚本概览

### 1. `ocr.py` - 单个文件OCR处理
**功能**: 处理单个图片文件，支持超时重试机制

**用法**:
```bash
python ocr.py input.png output.txt
python ocr.py --max-retries 5 --timeout 120 input.png output.txt
```

**参数**:
- `--max-retries N`: 最大重试次数 (默认: 3)
- `--timeout N`: 超时时间（秒）(默认: 60)
- `--backoff-factor N`: 退避因子 (默认: 2.0)
- `--language LANG`: 文本语言 (默认: English)

### 2. `batch_ocr.py` - 批量OCR处理（云API）
**功能**: 批量处理指定目录下的所有图片文件，支持并行处理

**用法**:
```bash
python batch_ocr.py --target-dir "目录名" --max-workers 10
python batch_ocr.py --target-dir "/绝对路径" --max-files 50
```

**参数**:
- `--target-dir DIR`: 目标目录（支持相对路径或绝对路径）
- `--max-workers N`: 并行处理线程数 (默认: 10)
- `--max-files N`: 最大处理文件数
- `--max-retries N`: 最大重试次数 (默认: 3)
- `--timeout N`: 超时时间（秒）(默认: 60)

### 3. `batch_ocr_ollama.py` - 批量OCR处理（本地Ollama）
**功能**: 使用本地Ollama模型进行批量OCR处理

**用法**:
```bash
python batch_ocr_ollama.py --target-dir "目录名" --model-name llava
```

**参数**:
- `--target-dir DIR`: 目标目录
- `--model-name NAME`: Ollama模型名称 (默认: llava)
- `--max-workers N`: 并行处理线程数 (默认: 10)

### 4. `batch_ocr_all.sh` - 批量处理所有目录
**功能**: 自动扫描output目录下的所有子目录并批量处理

**用法**:
```bash
./batch_ocr_all.sh
./batch_ocr_all.sh --max-workers 5
```

**参数**:
- `--max-workers N`: 设置最大并行度 (默认: 10)
- `--output-dir DIR`: 设置输出目录

### 5. `batch_ocr_smart.sh` - 智能批量处理
**功能**: 智能扫描目录，过滤空目录和系统文件，支持嵌套目录

**用法**:
```bash
./batch_ocr_smart.sh
./batch_ocr_smart.sh --min-png-count 10 --max-workers 5
```

**参数**:
- `--max-workers N`: 设置最大并行度 (默认: 10)
- `--min-png-count N`: 设置最少PNG文件数 (默认: 1)
- `--output-dir DIR`: 设置输出目录

### 6. `quick_ocr.sh` - 快速处理单个目录
**功能**: 快速处理指定目录，适合测试和调试

**用法**:
```bash
./quick_ocr.sh "目录名"
./quick_ocr.sh "2023年12月 A" 5
```

**参数**:
- 目录名: 要处理的目录名称
- 并行度: 可选的并行处理线程数 (默认: 10)

## 重试机制

所有脚本都支持智能重试机制：

### 错误类型识别
- **超时错误**: 包含 "timeout" 或 "timed out" 的错误
- **速率限制**: 包含 "rate limit" 或 "too many requests" 的错误
- **网络错误**: 包含 "network" 或 "connection" 的错误
- **服务器错误**: 包含 "server" 或 "internal" 的错误

### 退避策略
- 第1次尝试: 基础超时时间
- 第2次尝试: 基础超时时间 × 退避因子
- 第3次尝试: 基础超时时间 × 退避因子²
- 以此类推...

## 文件过滤

脚本会自动过滤以下文件：
- 系统文件（以 `._` 开头）
- 隐藏文件（以 `.` 开头）
- 空文件
- 过大的文件（超过20MB）

## 目录名处理

脚本正确处理包含空格的目录名：
- `"2023年12月 A"`
- `"2024年8月 亚太B"`
- `"北美2024年5月--数学 Module 2"`

## 日志记录

- 所有脚本都会记录详细的处理日志
- 日志文件位置: `/Volumes/ext/SatExams/data/ocr_batch.log`
- 智能脚本日志: `/Volumes/ext/SatExams/data/ocr_batch_smart.log`

## 使用建议

### 1. 首次使用
```bash
# 测试单个文件
python ocr.py test.png test.txt

# 测试单个目录
./quick_ocr.sh "2023年12月 A"
```

### 2. 批量处理
```bash
# 处理所有目录（推荐）
./batch_ocr_smart.sh --max-workers 5

# 处理特定目录
python batch_ocr.py --target-dir "2023年12月 A" --max-workers 3
```

### 3. 本地处理（需要Ollama）
```bash
# 确保Ollama服务运行
ollama serve

# 拉取模型
ollama pull llava

# 使用本地模型处理
python batch_ocr_ollama.py --target-dir "目录名"
```

## 故障排除

### 1. 虚拟环境问题
```bash
# 激活虚拟环境
source ../venv/bin/activate

# 检查Python版本
python --version
```

### 2. API密钥问题
```bash
# 设置环境变量
export OPENAI_API_KEY="your_key"
export OPENROUTER_API_KEY="your_key"
```

### 3. 权限问题
```bash
# 给脚本添加执行权限
chmod +x *.sh
```

### 4. 网络问题
- 检查网络连接
- 调整超时时间和重试次数
- 考虑使用本地Ollama模型

## 性能优化

### 1. 并行度设置
- 网络良好: 10-20个并行线程
- 网络一般: 5-10个并行线程
- 网络较差: 1-5个并行线程

### 2. 重试参数
- 网络不稳定: 增加重试次数和超时时间
- 网络稳定: 使用默认设置

### 3. 批量处理
- 小目录: 直接使用 `quick_ocr.sh`
- 大目录: 使用 `batch_ocr_smart.sh`
- 全部处理: 使用 `batch_ocr_all.sh`
