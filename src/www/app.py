#!/usr/bin/env python3
"""
SAT题目展示Web应用
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import os
from pathlib import Path

app = Flask(__name__)

# 数据库路径
DB_PATH = "/Volumes/ext/SatExams/data/types.db"

# 自定义过滤器：解析JSON字符串
@app.template_filter('from_json')
def from_json_filter(value):
    """将JSON字符串转换为Python对象"""
    try:
        import json
        return json.loads(value)
    except:
        return value

# SAT题型定义（从qtype.py复制）
QUESTION_TYPES = {
    "reading-evidence": "阅读证据题",
    "reading-words-in-context": "阅读词汇题", 
    "reading-command-of-evidence": "阅读理解题",
    "writing-lang-expression-of-ideas": "写作表达题",
    "writing-lang-grammar": "写作语法题",
    "writing-lang-command-of-evidence": "写作证据题",
    "writing-lang-words-in-context": "写作词汇题",
    "math-heart-of-algebra": "代数核心题",
    "math-problem-solving-data-analysis": "数据分析题",
    "math-passport-to-advanced-math": "高等数学题",
    "math-additional-topics": "附加数学题",
    "essay-analysis": "作文分析题"
}

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_question_types():
    """获取所有题型及其数量"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT question_type, COUNT(*) as count
        FROM questions 
        GROUP BY question_type 
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_questions_by_type(question_type, limit=100, order='time', start_question=1):
    """根据题型获取题目"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if order == 'random':
        # 随机排序
        cursor.execute("""
            SELECT id, file_path, question_id, question_type, content, options, confidence, add_time
            FROM questions 
            WHERE question_type = ? 
            AND (options IS NOT NULL AND LENGTH(options) >= 10)
            ORDER BY RANDOM()
            LIMIT ?
        """, (question_type, limit))
    else:
        # 按时间排序（默认），支持起始位置
        cursor.execute("""
            SELECT id, file_path, question_id, question_type, content, options, confidence, add_time
            FROM questions 
            WHERE question_type = ? 
            AND (options IS NOT NULL AND LENGTH(options) >= 10)
            ORDER BY add_time DESC
            LIMIT ? OFFSET ?
        """, (question_type, limit, start_question - 1))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

@app.route('/')
def index():
    """首页"""
    question_types = get_question_types()
    return render_template('index.html', question_types=question_types, type_descriptions=QUESTION_TYPES)

@app.route('/questions')
def questions():
    """题目展示页面"""
    question_type = request.args.get('type')
    limit = int(request.args.get('limit', 100))
    mode = request.args.get('mode', 'text')
    order = request.args.get('order', 'time')
    start_question = int(request.args.get('start_question', 1))
    
    if not question_type:
        return "请选择题目类型", 400
    
    # 如果是随机模式，忽略起始题目参数
    if order == 'random':
        start_question = 1
    
    questions = get_questions_by_type(question_type, limit, order, start_question)
    type_description = QUESTION_TYPES.get(question_type, question_type)
    
    if mode == 'images':
        return render_template('questions_images.html', 
                             questions=questions, 
                             question_type=question_type,
                             type_description=type_description,
                             total_count=len(questions),
                             order=order,
                             start_question=start_question)
    else:
        return render_template('questions.html', 
                             questions=questions, 
                             question_type=question_type,
                             type_description=type_description,
                             total_count=len(questions),
                             order=order,
                             start_question=start_question)

@app.route('/api/question_types')
def api_question_types():
    """API: 获取题型列表"""
    question_types = get_question_types()
    return jsonify([{
        'type': row['question_type'],
        'count': row['count'],
        'description': QUESTION_TYPES.get(row['question_type'], row['question_type'])
    } for row in question_types])

@app.route('/api/questions')
def api_questions():
    """API: 获取题目列表"""
    question_type = request.args.get('type')
    limit = int(request.args.get('limit', 100))
    order = request.args.get('order', 'time')
    start_question = int(request.args.get('start_question', 1))
    
    if not question_type:
        return jsonify({'error': '请选择题目类型'}), 400
    
    # 如果是随机模式，忽略起始题目参数
    if order == 'random':
        start_question = 1
    
    questions = get_questions_by_type(question_type, limit, order, start_question)
    
    return jsonify([{
        'id': row['id'],
        'file_path': row['file_path'],
        'question_id': row['question_id'],
        'question_type': row['question_type'],
        'content': row['content'],
        'options': row['options'],
        'confidence': row['confidence'],
        'add_time': row['add_time'],
        'png_path': row['file_path'].replace('.txt', '.png')
    } for row in questions])

@app.route('/static/images/<path:filename>')
def serve_image(filename):
    """提供图片文件服务"""
    # 构建完整的图片路径
    image_path = f"/Volumes/ext/SatExams/{filename}"
    
    if os.path.exists(image_path):
        # 如果图片存在，返回图片
        return send_from_directory(os.path.dirname(image_path), os.path.basename(image_path))
    else:
        # 如果图片不存在，返回占位符图片
        placeholder_path = "/Volumes/ext/SatExams/src/www/static/images/placeholder.svg"
        if os.path.exists(placeholder_path):
            return send_from_directory("/Volumes/ext/SatExams/src/www/static/images", "placeholder.svg")
        else:
            # 如果没有占位符图片，返回404
            return "图片不存在", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
