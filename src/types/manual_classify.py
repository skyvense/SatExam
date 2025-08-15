#!/usr/bin/env python3
"""
手动分类SAT题目
根据已识别的内容更新题型
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

# 手动识别的题型映射
MANUAL_CLASSIFICATIONS = {
    # 2023年12月 A
    "2023年12月 A/001.txt": ["title", "title", "title"],  # 考试说明
    "2023年12月 A/002.txt": ["words_in_context", "words_in_context", "words_in_context"],  # 词汇题
    "2023年12月 A/003.txt": ["skip"],  # OCR失败
    "2023年12月 A/004.txt": ["form_structure_and_sense", "form_structure_and_sense", "central_ideas_and_details"],  # 结构题和主旨题
    "2023年12月 A/005.txt": ["inference", "command_of_evidence_quantitative", "command_of_evidence_textual"],  # 推断、数据、证据
    "2023年12月 A/006.txt": ["command_of_evidence_quantitative", "command_of_evidence_textual", "inference"],  # 数据、证据、推断
    "2023年12月 A/007.txt": ["boundaries", "boundaries", "boundaries", "boundaries"],  # 语法题
    "2023年12月 A/008.txt": ["boundaries", "boundaries", "transitions", "transitions"],  # 语法和过渡词
    "2023年12月 A/009.txt": ["transitions", "rhetorical_synthesis", "rhetorical_synthesis"],  # 过渡词和整合
    "2023年12月 A/010.txt": ["rhetorical_synthesis", "words_in_context", "words_in_context"],  # 整合和词汇
    "2023年12月 A/011.txt": ["words_in_context", "words_in_context", "words_in_context"],  # 词汇题
    "2023年12月 A/012.txt": ["text_structure_and_purpose", "cross_text_connections"],  # 结构题和文本比较
    "2023年12月 A/013.txt": ["central_ideas_and_details", "inference"],  # 主旨题和推断
    "2023年12月 A/014.txt": ["central_ideas_and_details", "command_of_evidence_textual"],  # 主旨题和证据
    "2023年12月 A/015.txt": ["command_of_evidence_quantitative", "inference"],  # 数据题和推断
    "2023年12月 A/016.txt": ["inference", "boundaries", "boundaries"],  # 推断和语法
    "2023年12月 A/017.txt": ["boundaries", "boundaries", "boundaries", "boundaries"],  # 语法题
    "2023年12月 A/018.txt": ["transitions", "transitions", "transitions", "transitions"],  # 过渡词题
    "2023年12月 A/019.txt": ["transitions", "rhetorical_synthesis", "rhetorical_synthesis"],  # 过渡词和整合
    "2023年12月 A/020.txt": ["geometry", "statistics"],  # 几何和统计
    "2023年12月 A/021.txt": ["algebra", "coordinate_plane", "advanced_math", "algebra"],  # 代数、坐标、高等数学
    "2023年12月 A/022.txt": ["algebra", "word_problems", "data_analysis"],  # 代数、应用题、数据分析
    "2023年12月 A/023.txt": ["word_problems", "advanced_math", "advanced_math", "trigonometry"],  # 应用题、高等数学、三角
    "2023年12月 A/024.txt": ["coordinate_plane", "coordinate_plane", "geometry", "advanced_math"],  # 坐标、几何、高等数学
    "2023年12月 A/025.txt": ["algebra", "algebra", "advanced_math", "geometry", "word_problems"],  # 代数、高等数学、几何、应用题
    "2023年12月 A/026.txt": ["statistics", "algebra", "word_problems", "advanced_math"],  # 统计、代数、应用题、高等数学
    "2023年12月 A/027.txt": ["coordinate_plane", "word_problems", "algebra", "percents_and_ratios"],  # 坐标、应用题、代数、比例
    "2023年12月 A/028.txt": ["advanced_math", "advanced_math", "statistics", "algebra", "advanced_math"],  # 高等数学、统计、代数
    "2023年12月 A/029.txt": ["geometry", "algebra", "advanced_math", "powers_and_roots", "geometry"],  # 几何、代数、高等数学、根号、几何
    "2023年12月 A/030.txt": ["advanced_math", "word_problems", "advanced_math", "word_problems"],  # 高等数学、应用题
    "2023年12月 A/031.txt": ["title", "title", "title", "title"],  # 答案文件
    
    # 北美2024年5月--数学 Module 1
    "北美2024年5月--数学 Module 1/001.txt": ["statistics"],  # 概率统计
    "北美2024年5月--数学 Module 1/002.txt": ["algebra"],  # 不等式
    "北美2024年5月--数学 Module 1/003.txt": ["algebra"],  # 解方程
    "北美2024年5月--数学 Module 1/004.txt": ["geometry"],  # 三角形角度
    "北美2024年5月--数学 Module 1/005.txt": ["algebra"],  # 解方程
    "北美2024年5月--数学 Module 1/006.txt": ["trigonometry"],  # 三角函数
    "北美2024年5月--数学 Module 1/007.txt": ["title"],  # 答题说明
    "北美2024年5月--数学 Module 1/008.txt": ["data_analysis"],  # 图表分析
    "北美2024年5月--数学 Module 1/009.txt": ["geometry"],  # 几何计算
    "北美2024年5月--数学 Module 1/010.txt": ["statistics"],  # 统计比较
}

def update_database():
    """更新数据库中的题型"""
    db_path = Path("/Volumes/ext/SatExams/data/types.db")
    
    if not db_path.exists():
        print("数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        updated_count = 0
        
        for file_path, question_types in MANUAL_CLASSIFICATIONS.items():
            full_path = f"/Volumes/ext/SatExams/data/output/{file_path}"
            
            # 读取文件内容
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 解析JSON
                data = json.loads(content)
                questions = []
                
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, dict) and "content" in value:
                            questions.append({
                                "id": value.get("id", key),
                                "content": value.get("content", ""),
                                "options": value.get("options", {})
                            })
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "content" in item:
                            questions.append(item)
                
                # 更新数据库
                for i, question in enumerate(questions):
                    if i < len(question_types):
                        question_type = question_types[i]
                        
                        # 检查记录是否存在
                        cursor.execute("""
                            SELECT id FROM questions 
                            WHERE file_path = ? AND question_id = ?
                        """, (full_path, question["id"]))
                        
                        existing = cursor.fetchone()
                        
                        if existing:
                            # 更新现有记录
                            cursor.execute("""
                                UPDATE questions 
                                SET question_type = ?, confidence = 1.0, add_time = CURRENT_TIMESTAMP
                                WHERE file_path = ? AND question_id = ?
                            """, (question_type, full_path, question["id"]))
                            print(f"更新: {file_path} - 题目{question['id']} -> {question_type}")
                        else:
                            # 插入新记录
                            cursor.execute("""
                                INSERT INTO questions (file_path, question_id, question_type, content, options, confidence)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (full_path, question["id"], question_type, question["content"], json.dumps(question["options"]), 1.0))
                            print(f"插入: {file_path} - 题目{question['id']} -> {question_type}")
                        
                        updated_count += 1
                
                # 更新.type.txt文件
                type_file = Path(full_path).with_suffix('.type.txt')
                if len(question_types) > 1:
                    type_content = ','.join(question_types)
                else:
                    type_content = question_types[0]
                
                with open(type_file, 'w', encoding='utf-8') as f:
                    f.write(type_content)
                print(f"更新类型文件: {type_file.name}")
                
            except Exception as e:
                print(f"处理文件 {file_path} 失败: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"\n总共更新了 {updated_count} 条记录")
        
    except Exception as e:
        print(f"更新数据库失败: {e}")

if __name__ == "__main__":
    update_database()
