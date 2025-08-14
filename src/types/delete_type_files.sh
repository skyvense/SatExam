#!/bin/bash

# 删除所有目录下的001.type.txt文件
echo "开始删除所有目录下的001.type.txt文件..."

# 查找并删除所有001.type.txt文件
find "/Volumes/ext/SatExams/data/output" -name "001.type.txt" -type f -delete

echo "删除完成！"
echo "已删除的001.type.txt文件数量："
find "/Volumes/ext/SatExams/data/output" -name "001.type.txt" -type f | wc -l
