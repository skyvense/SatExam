#!/usr/bin/env python3
"""
清空SAT题型数据库
"""

import sqlite3
import os
from pathlib import Path

def clear_database():
    """清空数据库"""
    db_path = Path("/Volumes/ext/SatExams/data/types.db")
    
    if not db_path.exists():
        print("数据库文件不存在")
        return
    
    try:
        # 备份数据库
        backup_path = db_path.with_suffix('.db.backup')
        import shutil
        shutil.copy2(db_path, backup_path)
        print(f"数据库已备份到: {backup_path}")
        
        # 连接数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取表信息
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("当前数据库表:")
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  {table_name}: {count} 条记录")
        
        # 清空表
        for table in tables:
            table_name = table[0]
            cursor.execute(f"DELETE FROM {table_name}")
            print(f"已清空表: {table_name}")
        
        # 重置自增ID
        cursor.execute("DELETE FROM sqlite_sequence")
        
        conn.commit()
        conn.close()
        
        print("数据库清空完成！")
        
    except Exception as e:
        print(f"清空数据库失败: {e}")

if __name__ == "__main__":
    clear_database()
