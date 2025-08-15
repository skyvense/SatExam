#!/usr/bin/env python3
"""
修复数据库中的文件路径和exam_name字段
"""

import sqlite3
import os
from pathlib import Path

def fix_database_paths():
    """修复数据库中的文件路径和exam_name字段"""
    db_path = Path("/Volumes/ext/SatExams/data/types.db")
    
    if not db_path.exists():
        print("数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取所有记录
        cursor.execute("SELECT id, file_path FROM questions")
        records = cursor.fetchall()
        
        updated_count = 0
        
        for record_id, file_path in records:
            if file_path.startswith("/Volumes/ext/SatExams/data/output/"):
                # 提取相对路径
                relative_path = file_path.replace("/Volumes/ext/SatExams/data/output/", "")
                
                # 提取考试名称（第一个目录名）
                exam_name = relative_path.split("/")[0] if "/" in relative_path else "未知"
                
                # 更新数据库
                cursor.execute("""
                    UPDATE questions 
                    SET file_path = ?, exam_name = ?
                    WHERE id = ?
                """, (relative_path, exam_name, record_id))
                
                print(f"更新记录 {record_id}: {file_path} -> {relative_path} (考试: {exam_name})")
                updated_count += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n总共更新了 {updated_count} 条记录")
        
    except Exception as e:
        print(f"更新数据库失败: {e}")

if __name__ == "__main__":
    fix_database_paths()
