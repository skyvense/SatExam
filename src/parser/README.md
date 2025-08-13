# SAT PDF Parser

这是一个用于解析SAT考试PDF文件的Python工具。

## 功能特性

- 📄 扫描并识别数据目录中的所有PDF文件
- 📝 提取PDF文件中的文本内容
- 📊 分析SAT考试内容（阅读、写作、数学等部分）
- 📈 生成详细的分析报告
- 💾 保存分析结果到JSON文件
- 📋 生成摘要报告
- 🖼️ 将PDF按页分割为PNG图片
- 📁 自动复制原PDF到输出目录

## 安装依赖

首先激活虚拟环境：

```bash
cd src
source venv/bin/activate
```

然后安装依赖：

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本使用

```python
from pdf_parser import SATPDFParser

# 创建解析器实例
parser = SATPDFParser(data_dir="../data")

# 处理所有PDF文件
results = parser.process_all_pdfs()

# 保存结果
parser.save_results("my_results.json")

# 生成报告
report = parser.generate_summary_report()
print(report)
```

### 运行示例

```bash
# 运行主程序
python pdf_parser.py

# 运行使用示例
python example_usage.py

# 运行PDF分割器
python pdf_splitter.py input.pdf data/output --dpi 200

# 运行分割器示例
python example_splitter.py
```

## 输出文件

- `sat_analysis_results.json`: 详细的分析结果
- `sat_analysis_report.txt`: 摘要报告
- `parser.log`: 处理日志

## 分析内容

解析器会分析以下内容：

1. **文件信息**: 文件名、页数、文件大小、元数据
2. **文本内容**: 提取的文本内容预览
3. **内容分析**:
   - 总字符数和单词数
   - 检测的SAT部分（阅读、写作、数学、作文）
   - 估算的题目数量
   - 关键词识别

## PDF分割器

PDF分割器可以将单个PDF文件按页分割为PNG图片：

### 基本用法

```bash
python pdf_splitter.py <pdf_path> <output_root> [--dpi <dpi>]
```

### 参数说明

- `pdf_path` - PDF文件路径
- `output_root` - 输出根目录
- `--dpi` - 渲染DPI (默认: 200)

### 输出结构

```
data/output/
└── {filename}/
    ├── 001.png
    ├── 002.png
    ├── ...
    └── {filename}.pdf
```

### 示例

```bash
# 基本用法
python pdf_splitter.py input.pdf data/output

# 指定DPI
python pdf_splitter.py input.pdf data/output --dpi 300
```

## 自定义分析

你可以扩展 `analyze_sat_content` 方法来添加更多分析功能：

```python
def custom_analysis(self, text: str) -> Dict:
    # 添加你的自定义分析逻辑
    pass
```

## 注意事项

- 确保PDF文件没有被加密或受密码保护
- 某些PDF可能包含图片而非文本，提取效果可能有限
- 处理大量文件时可能需要较长时间

## 文件结构

```
src/parser/
├── pdf_parser.py          # 主解析器
├── pdf_splitter.py        # PDF分割器
├── example_usage.py       # 使用示例
├── example_splitter.py    # 分割器示例
├── requirements.txt       # 依赖列表
└── README.md             # 说明文档
```
