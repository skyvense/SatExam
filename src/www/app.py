#!/usr/bin/env python3
"""
SAT题目展示Web应用
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import os
import json
import requests
import urllib3
import ssl
import socket
from pathlib import Path
from config import OPENROUTER_API_KEY, OPENROUTER_MODEL, OPENROUTER_BASE_URL, DB_PATH

app = Flask(__name__)

# 数据库路径
DB_PATH = DB_PATH

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

def get_exam_names():
    """获取所有考试名称及其数量"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT exam_name, COUNT(*) as count
        FROM questions 
        WHERE exam_name IS NOT NULL
        GROUP BY exam_name 
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_questions_by_type(question_type, limit=100, order='time', start_question=1, exam_name=None):
    """根据题型获取题目"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 构建WHERE条件
    where_conditions = [
        "question_type = ?",
        "(options IS NOT NULL AND LENGTH(options) >= 10)"
    ]
    params = [question_type]
    
    # 如果指定了考试名称，添加过滤条件
    if exam_name and exam_name != "全部":
        where_conditions.append("exam_name = ?")
        params.append(exam_name)
    
    where_clause = " AND ".join(where_conditions)
    
    if order == 'random':
        # 随机排序
        cursor.execute(f"""
            SELECT id, file_path, question_id, question_type, content, options, confidence, add_time, exam_name
            FROM questions 
            WHERE {where_clause}
            ORDER BY RANDOM()
            LIMIT ?
        """, params + [limit])
    else:
        # 按时间排序（默认），支持起始位置
        cursor.execute(f"""
            SELECT id, file_path, question_id, question_type, content, options, confidence, add_time, exam_name
            FROM questions 
            WHERE {where_clause}
            ORDER BY add_time DESC
            LIMIT ? OFFSET ?
        """, params + [limit, start_question - 1])
    
    results = cursor.fetchall()
    conn.close()
    
    return results

@app.route('/')
def index():
    """首页"""
    question_types = get_question_types()
    exam_names = get_exam_names()
    return render_template('index.html', 
                         question_types=question_types, 
                         type_descriptions=QUESTION_TYPES,
                         exam_names=exam_names)

@app.route('/questions')
def questions():
    """题目展示页面"""
    question_type = request.args.get('type')
    limit = int(request.args.get('limit', 100))
    mode = request.args.get('mode', 'text')
    order = request.args.get('order', 'time')
    start_question = int(request.args.get('start_question', 1))
    exam_name = request.args.get('exam_name', '全部')
    
    if not question_type:
        return "请选择题目类型", 400
    
    # 如果是随机模式，忽略起始题目参数
    if order == 'random':
        start_question = 1
    
    questions = get_questions_by_type(question_type, limit, order, start_question, exam_name)
    type_description = QUESTION_TYPES.get(question_type, question_type)
    
    if mode == 'images':
        return render_template('questions_images.html', 
                             questions=questions, 
                             question_type=question_type,
                             type_description=type_description,
                             total_count=len(questions),
                             order=order,
                             start_question=start_question,
                             exam_name=exam_name)
    else:
        return render_template('questions.html', 
                             questions=questions, 
                             question_type=question_type,
                             type_description=type_description,
                             total_count=len(questions),
                             order=order,
                             start_question=start_question,
                             exam_name=exam_name)

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
    exam_name = request.args.get('exam_name', '全部')
    
    if not question_type:
        return jsonify({'error': '请选择题目类型'}), 400
    
    # 如果是随机模式，忽略起始题目参数
    if order == 'random':
        start_question = 1
    
    questions = get_questions_by_type(question_type, limit, order, start_question, exam_name)
    
    return jsonify([{
        'id': row['id'],
        'file_path': row['file_path'],
        'question_id': row['question_id'],
        'question_type': row['question_type'],
        'content': row['content'],
        'options': row['options'],
        'confidence': row['confidence'],
        'add_time': row['add_time'],
        'exam_name': row['exam_name'],
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

def check_answer_with_ai(question_content, options, user_answer):
    """使用AI检查答案"""
    try:
        print(f"开始AI检查，参数类型: question_content={type(question_content)}, options={type(options)}, user_answer={type(user_answer)}")
        print(f"question_content长度: {len(str(question_content))}")
        print(f"options内容: {options}")
        print(f"user_answer: {user_answer}")
        # 格式化选项
        if isinstance(options, dict):
            options_text = "\n".join([f"{key}. {value}" for key, value in options.items()])
        else:
            options_text = str(options)
        
        # 构建简化的提示词，避免编码问题
        prompt = f"Analyze this SAT question and check if the answer is correct.\n\nQuestion: {question_content}\n\nOptions:\n{options_text}\n\nUser's answer: {user_answer}\n\nPlease provide:\n1. Correct answer: [A/B/C/D]\n2. Is user's answer correct: [Yes/No]\n3. Solution steps: [detailed explanation]\n4. Key concepts: [main knowledge points]\n5. Suggestions: [improvement advice]"

        # 调用OpenRouter API
        headers = {
            'Authorization': f'Bearer {OPENROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://localhost:8080',
            'X-Title': 'SAT Answer Check'
        }
        
        data = {
            'model': OPENROUTER_MODEL,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,
            'max_tokens': 1000
        }
        
        # 使用json.dumps确保正确的编码
        import json
        json_data = json.dumps(data, ensure_ascii=False)
        
        # 使用requests发送请求
        response = requests.post(
            f'{OPENROUTER_BASE_URL}/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        print(f"API响应状态: {response.status_code}")
        print(f"API响应内容: {response.text[:200]}...")  # 只打印前200个字符
        
        if response.status_code == 200:
            response_data = response.json()
        else:
            return {
                'success': False,
                'error': f'API调用失败: {response.status_code} - {response.text[:100]}'
            }
        
        ai_response = response_data['choices'][0]['message']['content']
        return {
            'success': True,
            'analysis': ai_response
        }
            
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"AI检查错误详情: {error_trace}")
        print(f"错误类型: {type(e)}")
        print(f"错误信息: {str(e)}")
        return {
            'success': False,
            'error': f'检查答案时出错: {str(e)}'
        }

@app.route('/api/check_answer', methods=['POST'])
def api_check_answer():
    """API: 检查答案"""
    try:
        data = request.get_json()
        question_content = data.get('question_content')
        options = data.get('options')
        user_answer = data.get('user_answer')
        
        print(f"收到请求: question_content长度={len(str(question_content))}, options类型={type(options)}, user_answer={user_answer}")
        
        if not all([question_content, options, user_answer]):
            return jsonify({'error': '缺少必要参数'}), 400
        
        # 确保字符串是UTF-8编码
        if isinstance(question_content, str):
            question_content = question_content.encode('utf-8').decode('utf-8')
        if isinstance(user_answer, str):
            user_answer = user_answer.encode('utf-8').decode('utf-8')
        
        # 处理选项字典
        if isinstance(options, dict):
            for key, value in options.items():
                if isinstance(value, str):
                    options[key] = value.encode('utf-8').decode('utf-8')
        
        print(f"开始AI分析...")
        result = check_answer_with_ai(question_content, options, user_answer)
        print(f"AI分析完成: success={result.get('success')}")
        
        response = jsonify(result)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        return response
        
    except Exception as e:
        print(f"API错误: {str(e)}")
        return jsonify({'error': f'服务器错误: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
