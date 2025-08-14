#!/usr/bin/env python3
"""
SAT题型识别工具
使用AI分析题目文本，识别SAT考试的题型分类
支持新的JSON格式：区分题干和选项，一个文件可包含多道题
"""

import argparse
import json
import re
import sys
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import threading
import concurrent.futures
from queue import Queue

import openai

# SAT题型定义
QUESTION_TYPES = {
    # Reading题型
    "reading-evidence": {
        "keywords": ["evidence", "support", "best supports", "most strongly supports", "provides the best evidence"],
        "patterns": [r"which.*evidence", r"best.*supports", r"most strongly supports"],
        "description": "阅读证据题"
    },
    "reading-words-in-context": {
        "keywords": ["most nearly means", "as used", "closest in meaning", "best definition"],
        "patterns": [r"most nearly means", r"as used.*means", r"closest in meaning"],
        "description": "阅读词汇题"
    },
    "reading-command-of-evidence": {
        "keywords": ["command", "control", "author's purpose", "author's attitude", "tone"],
        "patterns": [r"author.*purpose", r"author.*attitude", r"tone.*passage"],
        "description": "阅读理解题"
    },
    
    # Writing题型
    "writing-lang-expression-of-ideas": {
        "keywords": ["expression", "ideas", "development", "organization", "effective", "improve"],
        "patterns": [r"expression.*ideas", r"development.*organization", r"most effective"],
        "description": "写作表达题"
    },
    "writing-lang-grammar": {
        "keywords": ["grammar", "punctuation", "sentence structure", "verb tense", "subject-verb agreement"],
        "patterns": [r"grammar", r"punctuation", r"verb.*tense", r"subject.*verb"],
        "description": "写作语法题"
    },
    "writing-lang-command-of-evidence": {
        "keywords": ["evidence", "support", "argument", "claim", "reasoning"],
        "patterns": [r"evidence.*argument", r"support.*claim", r"reasoning"],
        "description": "写作证据题"
    },
    "writing-lang-words-in-context": {
        "keywords": ["vocabulary", "word choice", "precise", "appropriate", "context"],
        "patterns": [r"vocabulary", r"word.*choice", r"precise.*word"],
        "description": "写作词汇题"
    },
    
    # Math题型
    "math-heart-of-algebra": {
        "keywords": ["equation", "inequality", "linear", "quadratic", "function", "graph", "slope", "intercept"],
        "patterns": [r"equation", r"inequality", r"linear.*function", r"slope", r"intercept"],
        "description": "代数核心题"
    },
    "math-problem-solving-data-analysis": {
        "keywords": ["data", "table", "chart", "graph", "statistics", "mean", "median", "percent", "ratio"],
        "patterns": [r"data.*table", r"chart.*graph", r"statistics", r"mean.*median"],
        "description": "数据分析题"
    },
    "math-passport-to-advanced-math": {
        "keywords": ["polynomial", "quadratic", "exponential", "radical", "complex", "advanced"],
        "patterns": [r"polynomial", r"quadratic.*equation", r"exponential", r"radical"],
        "description": "高等数学题"
    },
    "math-additional-topics": {
        "keywords": ["geometry", "trigonometry", "circle", "triangle", "volume", "area", "angle"],
        "patterns": [r"geometry", r"trigonometry", r"circle.*area", r"triangle.*angle"],
        "description": "附加数学题"
    },
    
    # Essay题型
    "essay-analysis": {
        "keywords": ["essay", "analysis", "argument", "evaluate", "persuasive", "rhetorical"],
        "patterns": [r"essay.*analysis", r"evaluate.*argument", r"persuasive.*techniques"],
        "description": "作文分析题"
    }
}


class QuestionTypeAnalyzer:
    """题型分析器"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.question_types = QUESTION_TYPES
        
        # 初始化AI客户端
        self.api_key = api_key or os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        if self.api_key:
            # 配置OpenAI客户端
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url="https://openrouter.ai/api/v1"  # 使用OpenRouter
            )
        else:
            self.client = None
        
        # 数据库路径
        self.db_path = Path("/Volumes/ext/SatExams/data/types.db")
        self.db_path.parent.mkdir(exist_ok=True)
        
        # 线程锁
        self.db_lock = threading.Lock()
        
        # 初始化数据库
        self._init_database()
    
    def _init_database(self):
        """初始化数据库 - 支持新的JSON格式"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 创建新的题目表结构
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    question_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    options TEXT,
                    confidence REAL DEFAULT 0.0,
                    add_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(file_path, question_id)
                )
            ''')
            
            # 保留旧表以兼容现有数据
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS question_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    png_path TEXT NOT NULL,
                    question_type TEXT NOT NULL,
                    txt_content TEXT,
                    add_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            print(f"数据库初始化成功: {self.db_path}")
        except Exception as e:
            print(f"数据库初始化失败: {e}")
    
    def parse_json_content(self, content: str) -> List[Dict[str, Any]]:
        """
        解析JSON格式的题目内容
        
        Args:
            content: JSON格式的题目内容
            
        Returns:
            题目列表，每个题目包含id, content, options
        """
        try:
            data = json.loads(content)
            questions = []
            
            if isinstance(data, dict):
                # 检查是否是单题目格式: {"id": "...", "content": "...", "options": {...}}
                if "id" in data and "content" in data:
                    # 单题目格式
                    question = {
                        "id": data.get("id", "unknown"),
                        "content": data.get("content", ""),
                        "options": data.get("options", {})
                    }
                    questions.append(question)
                else:
                    # 多题目格式: {"key": {"id": "...", "content": "...", "options": {...}}}
                    for question_id, question_data in data.items():
                        if isinstance(question_data, dict):
                            # 跳过指令性内容和标题
                            skip_keywords = ["Instructions", "partial_top", "title", "header", "Header/Directions", "Footer", "IMPORTANT REMINDERS"]
                            content = question_data.get("content", "").lower()
                            if (question_id in skip_keywords or 
                                "instruction" in content or 
                                "copyright" in content or 
                                "college board" in content or
                                "page" in content and len(content) < 100):
                                continue
                            question = {
                                "id": question_data.get("id", question_id),
                                "content": question_data.get("content", ""),
                                "options": question_data.get("options", {})
                            }
                            questions.append(question)
            elif isinstance(data, list):
                # 数组格式: [{"id": "...", "content": "...", "options": {...}}]
                for question_data in data:
                    if isinstance(question_data, dict):
                        # 跳过指令性内容和标题
                        skip_keywords = ["Instructions", "title", "header", "Header/Directions", "Footer", "IMPORTANT REMINDERS"]
                        content = question_data.get("content", "").lower()
                        if (question_data.get("id") in skip_keywords or 
                            "instruction" in content or 
                            "copyright" in content or 
                            "college board" in content or
                            "page" in content and len(content) < 100):
                            continue
                        question = {
                            "id": question_data.get("id", "unknown"),
                            "content": question_data.get("content", ""),
                            "options": question_data.get("options", {})
                        }
                        questions.append(question)
            
            return questions
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            # 如果不是JSON格式，尝试作为单个题目处理
            return [{"id": "1", "content": content, "options": {}}]
        except Exception as e:
            print(f"解析题目内容失败: {e}")
            return []
    
    def save_questions_to_database(self, file_path: str, questions: List[Dict[str, Any]], question_types: List[str], confidences: List[float] = None):
        """
        保存题目到数据库
        
        Args:
            file_path: 文件路径
            questions: 题目列表
            question_types: 对应的题型列表
            confidences: 对应的置信度列表
        """
        with self.db_lock:  # 使用线程锁保护数据库操作
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                for i, question in enumerate(questions):
                    question_id = question["id"]
                    content = question["content"]
                    options = json.dumps(question["options"], ensure_ascii=False)
                    question_type = question_types[i] if i < len(question_types) else "unknown"
                    confidence = confidences[i] if confidences and i < len(confidences) else 0.8
                    
                    # 检查是否已存在
                    cursor.execute("""
                        SELECT id FROM questions 
                        WHERE file_path = ? AND question_id = ?
                    """, (file_path, question_id))
                    
                    existing = cursor.fetchone()
                    
                    if existing:
                        # 更新现有记录
                        cursor.execute("""
                            UPDATE questions 
                            SET question_type = ?, content = ?, options = ?, 
                                confidence = ?, add_time = CURRENT_TIMESTAMP
                            WHERE file_path = ? AND question_id = ?
                        """, (question_type, content, options, confidence, file_path, question_id))
                        print(f"更新题目: {file_path} - {question_id}")
                    else:
                        # 插入新记录
                        cursor.execute("""
                            INSERT INTO questions (file_path, question_id, question_type, content, options, confidence)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (file_path, question_id, question_type, content, options, confidence))
                        print(f"插入题目: {file_path} - {question_id}")
                
                conn.commit()
                conn.close()
                
            except Exception as e:
                print(f"保存到数据库失败: {e}")
    
    def get_questions_from_database(self, file_path: str = None) -> List[Dict]:
        """
        从数据库获取题目
        
        Args:
            file_path: 可选的文件路径，如果为None则获取所有记录
            
        Returns:
            题目列表
        """
        with self.db_lock:  # 使用线程锁保护数据库操作
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                if file_path:
                    cursor.execute("""
                        SELECT id, file_path, question_id, question_type, content, options, confidence, add_time
                        FROM questions WHERE file_path = ?
                        ORDER BY question_id
                    """, (file_path,))
                else:
                    cursor.execute("""
                        SELECT id, file_path, question_id, question_type, content, options, confidence, add_time
                        FROM questions ORDER BY add_time DESC
                    """)
                
                results = []
                for row in cursor.fetchall():
                    options = json.loads(row[5]) if row[5] else {}
                    results.append({
                        "id": row[0],
                        "file_path": row[1],
                        "question_id": row[2],
                        "question_type": row[3],
                        "content": row[4],
                        "options": options,
                        "confidence": row[6],
                        "add_time": row[7]
                    })
                
                conn.close()
                return results
                
            except Exception as e:
                print(f"从数据库获取数据失败: {e}")
                return []
    
    def save_to_database(self, png_path: str, question_type: str, txt_content: str = None):
        """
        保存题型分析结果到数据库（兼容旧格式）
        
        Args:
            png_path: PNG文件路径（相对于data目录）
            question_type: 识别的题型
            txt_content: 文本内容
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 检查是否已存在
            cursor.execute("SELECT id FROM question_types WHERE png_path = ?", (png_path,))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有记录
                cursor.execute("""
                    UPDATE question_types 
                    SET question_type = ?, txt_content = ?, add_time = CURRENT_TIMESTAMP
                    WHERE png_path = ?
                """, (question_type, txt_content, png_path))
                print(f"更新数据库记录: {png_path}")
            else:
                # 插入新记录
                cursor.execute("""
                    INSERT INTO question_types (png_path, question_type, txt_content)
                    VALUES (?, ?, ?)
                """, (png_path, question_type, txt_content))
                print(f"插入数据库记录: {png_path}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"保存到数据库失败: {e}")
    
    def get_from_database(self, png_path: str = None) -> List[Dict]:
        """
        从数据库获取题型分析结果（兼容旧格式）
        
        Args:
            png_path: 可选的PNG文件路径，如果为None则获取所有记录
            
        Returns:
            结果列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if png_path:
                cursor.execute("""
                    SELECT id, png_path, question_type, txt_content, add_time
                    FROM question_types WHERE png_path = ?
                """, (png_path,))
            else:
                cursor.execute("""
                    SELECT id, png_path, question_type, txt_content, add_time
                    FROM question_types ORDER BY add_time DESC
                """)
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "id": row[0],
                    "png_path": row[1],
                    "question_type": row[2],
                    "txt_content": row[3],
                    "add_time": row[4]
                })
            
            conn.close()
            return results
            
        except Exception as e:
            print(f"从数据库获取数据失败: {e}")
            return []
    
    def analyze_text(self, text: str) -> Dict[str, float]:
        """
        分析文本，返回各题型的匹配分数
        
        Args:
            text: 题目文本
            
        Returns:
            题型匹配分数字典
        """
        text_lower = text.lower()
        scores = {}
        
        for qtype, config in self.question_types.items():
            score = 0
            
            # 关键词匹配
            for keyword in config["keywords"]:
                if keyword.lower() in text_lower:
                    score += 1
            
            # 正则表达式匹配
            for pattern in config["patterns"]:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 2  # 正则匹配权重更高
            
            # 特殊规则
            score += self._apply_special_rules(qtype, text_lower)
            
            scores[qtype] = score
        
        return scores
    
    def _apply_special_rules(self, qtype: str, text: str) -> int:
        """应用特殊规则"""
        score = 0
        
        if qtype == "reading-evidence":
            # 阅读证据题通常有"which choice provides the best evidence"
            if "which choice" in text and "evidence" in text:
                score += 3
        
        elif qtype == "reading-words-in-context":
            # 词汇题通常有"most nearly means"
            if "most nearly means" in text:
                score += 3
        
        elif qtype.startswith("math-"):
            # 数学题通常有数字、公式、图表
            if re.search(r'\d+', text) or re.search(r'[+\-*/=]', text):
                score += 1
            if any(word in text for word in ["graph", "table", "chart"]):
                score += 1
        
        elif qtype == "essay-analysis":
            # 作文题通常较长，有分析要求
            if len(text) > 200 and "analysis" in text:
                score += 2
        
        return score
    
    def classify_question(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """
        分类题目
        
        Args:
            text: 题目文本
            
        Returns:
            (最佳题型, 置信度, 所有分数)
        """
        # 优先使用AI分析
        if self.client:
            try:
                return self._ai_classify_question(text)
            except Exception as e:
                print(f"AI分析失败，使用规则分析: {e}")
        
        # 回退到规则分析
        return self._rule_classify_question(text)
    
    def _ai_classify_question(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """使用AI分析题型"""
        
        prompt = f"""
请分析以下SAT考试题目，识别其题型。请从以下题型中选择最合适的一个：

**Reading题型:**
- reading-evidence: 阅读证据题（要求选择支持论点的证据）
- reading-words-in-context: 阅读词汇题（要求解释词汇在上下文中的含义）
- reading-command-of-evidence: 阅读理解题（要求理解作者意图、态度等）

**Writing题型:**
- writing-lang-expression-of-ideas: 写作表达题（关于表达、组织、发展观点）
- writing-lang-grammar: 写作语法题（关于语法、标点、句子结构）
- writing-lang-command-of-evidence: 写作证据题（关于论证、证据、推理）
- writing-lang-words-in-context: 写作词汇题（关于词汇选择、精确表达）

**Math题型:**
- math-heart-of-algebra: 代数核心题（方程、不等式、线性函数等）
- math-problem-solving-data-analysis: 数据分析题（图表、统计、百分比等）
- math-passport-to-advanced-math: 高等数学题（多项式、二次方程、指数等）
- math-additional-topics: 附加数学题（几何、三角、圆、三角形等）

**Essay题型:**
- essay-analysis: 作文分析题（分析论证、评估论点等）

请只返回题型代码，不要其他内容。

题目内容：
{text}
"""

        try:
            response = self.client.chat.completions.create(
                model="anthropic/claude-3-5-sonnet",  # 使用Claude模型
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            ai_result = response.choices[0].message.content.strip().lower()
            
            # 验证AI返回的结果是否在预定义题型中
            if ai_result in self.question_types:
                return ai_result, 0.95, {ai_result: 10}  # AI分析置信度很高
            else:
                print(f"AI返回未知题型: {ai_result}")
                return self._rule_classify_question(text)
                
        except Exception as e:
            print(f"AI分析异常: {e}")
            return self._rule_classify_question(text)
    
    def _rule_classify_question(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """使用规则分析题型（回退方法）"""
        scores = self.analyze_text(text)
        
        if not scores:
            return "unknown", 0.0, scores
        
        # 找到最高分数
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # 计算置信度 (0-1)
        total_score = sum(scores.values())
        confidence = best_score / total_score if total_score > 0 else 0
        
        return best_type, confidence, scores
    
    def analyze_file(self, file_path: Path, save_to_db: bool = True, force_reanalyze: bool = False, skip_cached: bool = False) -> Dict:
        """
        分析单个文件
        
        Args:
            file_path: 文本文件路径
            save_to_db: 是否保存到数据库
            force_reanalyze: 是否强制重新分析（忽略.type.txt文件）
            skip_cached: 是否跳过已存在.type.txt文件的处理
            
        Returns:
            分析结果字典
        """
        try:
            # 读取文件内容
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尝试解析为JSON格式
            questions = self.parse_json_content(content)
            
            if len(questions) > 1:
                # 多题目文件
                print(f"  检测到 {len(questions)} 道题目")
                question_types = []
                confidences = []
                results = []
                
                # 检查是否存在.type.txt文件
                type_file = file_path.with_suffix('.type.txt')
                if type_file.exists() and not force_reanalyze:
                    if skip_cached:
                        # 如果设置了跳过缓存，直接返回跳过信息
                        return {
                            "filename": file_path.name,
                            "filepath": str(file_path),
                            "skipped": True,
                            "reason": "type_file_exists"
                        }
                    
                    # 如果.type.txt文件存在且不强制重新分析，直接读取
                    with open(type_file, 'r', encoding='utf-8') as f:
                        saved_types = f.read().strip().split(',')
                    
                    # 使用保存的题型
                    for i, question in enumerate(questions):
                        question_text = question["content"]
                        if i < len(saved_types):
                            qtype = saved_types[i]
                            confidence = 1.0  # 从文件读取的置信度为1.0
                        else:
                            qtype, confidence, scores = self.classify_question(question_text)
                        
                        question_types.append(qtype)
                        confidences.append(confidence)
                        
                        result = {
                            "question_id": question["id"],
                            "question_type": qtype,
                            "confidence": confidence,
                            "scores": {qtype: 10} if confidence == 1.0 else {},
                            "content": question_text,
                            "options": question["options"],
                            "text_preview": question_text[:200] + "..." if len(question_text) > 200 else question_text
                        }
                        results.append(result)
                    
                    print(f"  从.type.txt文件读取题型: {','.join(saved_types)}")
                    
                    # 保存到新数据库格式
                    if save_to_db:
                        self.save_questions_to_database(str(file_path), questions, question_types, confidences)
                    
                    return {
                        "filename": file_path.name,
                        "filepath": str(file_path),
                        "question_count": len(questions),
                        "questions": results,
                        "source": "type_file"
                    }
                
                for i, question in enumerate(questions):
                    question_text = question["content"]
                    qtype, confidence, scores = self.classify_question(question_text)
                    question_types.append(qtype)
                    confidences.append(confidence)
                    
                    result = {
                        "question_id": question["id"],
                        "question_type": qtype,
                        "confidence": confidence,
                        "scores": scores,
                        "content": question_text,
                        "options": question["options"],
                        "text_preview": question_text[:200] + "..." if len(question_text) > 200 else question_text
                    }
                    results.append(result)
                
                # 保存到新数据库格式
                if save_to_db:
                    self.save_questions_to_database(str(file_path), questions, question_types, confidences)
                
                # 为多题目文件生成.type.txt文件（包含所有题型）
                try:
                    type_file = file_path.with_suffix('.type.txt')
                    # 将多个题型用逗号分隔保存
                    all_types = ','.join(question_types)
                    with open(type_file, 'w', encoding='utf-8') as f:
                        f.write(all_types)
                    print(f"  保存题型到文件: {type_file.name} ({all_types})")
                except Exception as e:
                    print(f"  保存.type.txt文件失败: {e}")
                
                return {
                    "filename": file_path.name,
                    "filepath": str(file_path),
                    "question_count": len(questions),
                    "questions": results,
                    "source": "json_multi_questions"
                }
            else:
                # 单题目文件或非JSON格式
                question = questions[0]
                question_text = question["content"]
                
                # 检查是否存在.type.txt文件
                type_file = file_path.with_suffix('.type.txt')
                if type_file.exists() and not force_reanalyze:
                    if skip_cached:
                        # 如果设置了跳过缓存，直接返回跳过信息
                        return {
                            "filename": file_path.name,
                            "filepath": str(file_path),
                            "skipped": True,
                            "reason": "type_file_exists"
                        }
                    
                    # 如果.type.txt文件存在且不强制重新分析，直接读取
                    with open(type_file, 'r', encoding='utf-8') as f:
                        qtype = f.read().strip()
                    
                    result = {
                        "filename": file_path.name,
                        "filepath": str(file_path),
                        "question_type": qtype,
                        "confidence": 1.0,  # 从文件读取的置信度为1.0
                        "scores": {qtype: 10},  # 模拟分数
                        "text_preview": question_text[:200] + "..." if len(question_text) > 200 else question_text,
                        "source": "type_file"  # 标记来源
                    }
                    
                    print(f"  从.type.txt文件读取题型: {qtype}")
                else:
                    # 进行AI分析
                    qtype, confidence, scores = self.classify_question(question_text)
                    
                    result = {
                        "filename": file_path.name,
                        "filepath": str(file_path),
                        "question_type": qtype,
                        "confidence": confidence,
                        "scores": scores,
                        "text_preview": question_text[:200] + "..." if len(question_text) > 200 else question_text,
                        "source": "ai_analysis"  # 标记来源
                    }
                    
                    # 保存题型到.type.txt文件
                    try:
                        with open(type_file, 'w', encoding='utf-8') as f:
                            f.write(qtype)
                        print(f"  保存题型到文件: {type_file.name}")
                    except Exception as e:
                        print(f"  保存.type.txt文件失败: {e}")
                
                # 保存到新数据库格式
                if save_to_db and "error" not in result:
                    # 对于JSON格式的单题目文件，也使用新格式数据库
                    if len(questions) == 1 and question["content"]:
                        self.save_questions_to_database(
                            str(file_path), 
                            [question], 
                            [result['question_type']], 
                            [result['confidence']]
                        )
                    else:
                        # 对于非JSON格式文件，使用旧格式数据库
                        png_path = str(file_path).replace('.txt', '.png')
                        data_root = Path("/Volumes/ext/SatExams/data")
                        try:
                            relative_png_path = str(Path(png_path).relative_to(data_root))
                            self.save_to_database(relative_png_path, result['question_type'], question_text)
                        except ValueError:
                            # 如果无法计算相对路径，使用绝对路径
                            self.save_to_database(png_path, result['question_type'], question_text)
                
                return result
            
        except Exception as e:
            return {
                "filename": file_path.name,
                "filepath": str(file_path),
                "error": str(e)
            }
    
    def batch_analyze(self, directory: Path, pattern: str = "*.txt", max_files: Optional[int] = None, force_reanalyze: bool = False, batch_size: int = 50, max_workers: int = 5, skip_cached: bool = False) -> List[Dict]:
        """
        批量分析目录中的文件（支持多线程）
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            max_files: 最大处理文件数
            force_reanalyze: 是否强制重新分析（忽略.type.txt文件）
            batch_size: 批量处理大小，每次处理多少个文件
            max_workers: 最大线程数
            skip_cached: 是否跳过已存在.type.txt文件的处理
            
        Returns:
            分析结果列表
        """
        results = []
        
        if not directory.exists():
            print(f"目录不存在: {directory}")
            return results
        
        txt_files = list(directory.rglob(pattern))
        total_files = len(txt_files)
        
        # 过滤文件：只保留主要的.txt文件，排除.type.txt和系统文件
        txt_files = [f for f in txt_files if 
                    f.name.endswith('.txt') and 
                    not f.name.endswith('.type.txt') and 
                    not f.name.startswith('._')]
        
        # 自然排序文件（按数字顺序）
        def natural_sort_key(file_path):
            # 提取文件名中的数字部分进行排序
            filename = file_path.name
            # 移除扩展名
            name_without_ext = filename.rsplit('.', 1)[0]
            # 提取数字部分
            import re
            numbers = re.findall(r'\d+', name_without_ext)
            if numbers:
                # 返回第一个数字作为排序键
                return int(numbers[0])
            else:
                # 如果没有数字，按文件名排序
                return filename
        
        # 按自然顺序排序
        txt_files.sort(key=natural_sort_key)
        
        # 限制文件数量
        if max_files:
            txt_files = txt_files[:max_files]
            print(f"找到 {total_files} 个文本文件，将处理前 {max_files} 个")
        else:
            print(f"找到 {total_files} 个文本文件")
        
        # 线程安全的分析单个文件
        def analyze_file_thread_safe(file_path: Path) -> Tuple[int, Dict]:
            try:
                result = self.analyze_file(file_path, force_reanalyze=force_reanalyze, skip_cached=skip_cached)
                return (txt_files.index(file_path) + 1, result)
            except Exception as e:
                return (txt_files.index(file_path) + 1, {"error": str(e), "filename": file_path.name})
        
        # 多线程处理
        results = [None] * len(txt_files)  # 预分配结果列表
        completed_count = 0
        lock = threading.Lock()
        
        def update_progress(index: int, result: Dict):
            nonlocal completed_count
            with lock:
                results[index - 1] = result
                completed_count += 1
                
                # 显示进度
                if "skipped" in result:
                    # 跳过的文件
                    print(f"[{index}/{len(txt_files)}] 跳过: {result['filename']} - {result['reason']}")
                elif "error" not in result:
                    if "questions" in result:
                        # 多题目文件
                        print(f"[{index}/{len(txt_files)}] 分析: {result['filename']} - 题目数量: {result['question_count']}")
                        for j, question in enumerate(result['questions'], 1):
                            print(f"    题目{j}: {question['question_type']} (置信度: {question['confidence']:.2f})")
                    else:
                        # 单题目文件
                        print(f"[{index}/{len(txt_files)}] 分析: {result['filename']} - 题型: {result['question_type']} (置信度: {result['confidence']:.2f})")
                else:
                    print(f"[{index}/{len(txt_files)}] 分析: {result['filename']} - 错误: {result['error']}")
                
                print(f"进度: {completed_count}/{len(txt_files)} ({completed_count/len(txt_files)*100:.1f}%)")
        
        print(f"开始多线程处理，使用 {max_workers} 个线程...")
        
        # 使用线程池执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_file = {executor.submit(analyze_file_thread_safe, file_path): file_path for file_path in txt_files}
            
            # 处理完成的任务
            for future in concurrent.futures.as_completed(future_to_file):
                index, result = future.result()
                update_progress(index, result)
        
        return results
    
    def save_results(self, results: List[Dict], output_file: str = "question_types.json"):
        """保存分析结果"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            print(f"结果已保存到: {output_file}")
        except Exception as e:
            print(f"保存失败: {e}")
    
    def generate_summary(self, results: List[Dict]) -> str:
        """生成摘要报告"""
        if not results:
            return "没有分析结果"
        
        # 统计题型分布
        type_counts = {}
        total_files = 0
        total_questions = 0
        skipped_files = 0
        
        for result in results:
            if "skipped" in result:
                # 跳过的文件
                skipped_files += 1
                continue
            elif "error" not in result:
                if "questions" in result:
                    # 多题目文件
                    total_files += 1
                    for question in result["questions"]:
                        qtype = question["question_type"]
                        type_counts[qtype] = type_counts.get(qtype, 0) + 1
                        total_questions += 1
                else:
                    # 单题目文件
                    qtype = result["question_type"]
                    type_counts[qtype] = type_counts.get(qtype, 0) + 1
                    total_files += 1
                    total_questions += 1
        
        # 生成报告
        report = f"""
SAT题型分析报告
================

总文件数: {total_files}
总题目数: {total_questions}
成功分析: {len([r for r in results if "error" not in r and "skipped" not in r])}
分析失败: {len([r for r in results if "error" in r])}
跳过文件: {skipped_files}

题型分布:
"""
        
        for qtype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_questions) * 100 if total_questions > 0 else 0
            description = self.question_types.get(qtype, {}).get("description", "未知题型")
            report += f"  {qtype}: {count} 题 ({percentage:.1f}%) - {description}\n"
        
        return report

    def generate_database_summary(self) -> str:
        """生成数据库统计报告"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 获取旧表统计
            cursor.execute("SELECT COUNT(*) FROM question_types")
            old_total_count = cursor.fetchone()[0]
            
            # 获取新表统计
            cursor.execute("SELECT COUNT(*) FROM questions")
            new_total_count = cursor.fetchone()[0]
            
            # 获取新表题型分布
            cursor.execute("""
                SELECT question_type, COUNT(*) as count
                FROM questions 
                GROUP BY question_type 
                ORDER BY count DESC
            """)
            new_type_distribution = cursor.fetchall()
            
            # 获取旧表题型分布
            cursor.execute("""
                SELECT question_type, COUNT(*) as count
                FROM question_types 
                GROUP BY question_type 
                ORDER BY count DESC
            """)
            old_type_distribution = cursor.fetchall()
            
            # 获取最新记录
            cursor.execute("""
                SELECT file_path, question_id, question_type, add_time
                FROM questions 
                ORDER BY add_time DESC 
                LIMIT 5
            """)
            recent_records = cursor.fetchall()
            
            conn.close()
            
            # 生成报告
            report = f"""
数据库题型分析报告
==================

旧格式记录数: {old_total_count}
新格式记录数: {new_total_count}
总记录数: {old_total_count + new_total_count}

新格式题型分布:
"""
            for qtype, count in new_type_distribution:
                percentage = (count / new_total_count) * 100 if new_total_count > 0 else 0
                description = self.question_types.get(qtype, {}).get("description", "未知题型")
                report += f"  {qtype}: {count} 题 ({percentage:.1f}%) - {description}\n"
            
            if old_type_distribution:
                report += "\n旧格式题型分布:\n"
                for qtype, count in old_type_distribution:
                    percentage = (count / old_total_count) * 100 if old_total_count > 0 else 0
                    description = self.question_types.get(qtype, {}).get("description", "未知题型")
                    report += f"  {qtype}: {count} 题 ({percentage:.1f}%) - {description}\n"
            
            report += "\n最新记录:\n"
            for file_path, question_id, qtype, add_time in recent_records:
                report += f"  {file_path} - {question_id} -> {qtype} ({add_time})\n"
            
            return report
            
        except Exception as e:
            return f"生成数据库报告失败: {e}"


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SAT题型识别工具")
    parser.add_argument("input", type=str, nargs='?', help="输入文件或目录路径")
    parser.add_argument("--output", "-o", type=str, default="question_types.json", 
                       help="输出文件 (默认: question_types.json)")
    parser.add_argument("--pattern", "-p", type=str, default="*.txt",
                       help="文件匹配模式 (默认: *.txt)")
    parser.add_argument("--api-key", type=str, help="OpenAI或OpenRouter API密钥")
    parser.add_argument("--no-ai", action="store_true", help="禁用AI分析，仅使用规则分析")
    parser.add_argument("--max-files", "-m", type=int, help="最大处理文件数")
    parser.add_argument("--batch-size", "-b", type=int, default=50, help="批量处理大小，每次处理多少个文件 (默认: 50)")
    parser.add_argument("--max-workers", "-w", type=int, default=5, help="最大线程数 (默认: 5)")
    parser.add_argument("--force-reanalyze", action="store_true", help="强制重新分析，忽略.type.txt文件")
    parser.add_argument("--skip-cached", action="store_true", help="跳过已存在.type.txt文件的处理，不更新数据库")
    
    # 数据库相关选项
    parser.add_argument("--db-query", action="store_true", help="查询数据库中的所有记录")
    parser.add_argument("--db-summary", action="store_true", help="生成数据库统计报告")
    parser.add_argument("--db-path", type=str, help="查询特定PNG文件的题型")
    parser.add_argument("--db-questions", action="store_true", help="查询新格式数据库中的所有题目")
    parser.add_argument("--db-file", type=str, help="查询特定文件的题目")
    
    args = parser.parse_args()
    
    # 检查API密钥
    api_key = args.api_key or os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
    if not api_key and not args.no_ai:
        print("⚠️  未提供API密钥，将使用规则分析")
        print("请设置环境变量 OPENAI_API_KEY 或 OPENROUTER_API_KEY")
        print("或使用 --api-key 参数提供密钥")
        print("或使用 --no-ai 参数禁用AI分析")
    
    analyzer = QuestionTypeAnalyzer(api_key=api_key if not args.no_ai else None)
    
    # 数据库查询功能
    if args.db_query:
        print("=== 数据库查询 ===")
        results = analyzer.get_from_database()
        print(f"总记录数: {len(results)}")
        for result in results[:10]:  # 显示前10条
            print(f"  {result['png_path']} -> {result['question_type']} ({result['add_time']})")
        if len(results) > 10:
            print(f"  ... 还有 {len(results) - 10} 条记录")
        return
    
    if args.db_summary:
        print("=== 数据库统计报告 ===")
        summary = analyzer.generate_database_summary()
        print(summary)
        return
    
    if args.db_path:
        print(f"=== 查询PNG文件: {args.db_path} ===")
        results = analyzer.get_from_database(args.db_path)
        if results:
            for result in results:
                print(f"题型: {result['question_type']}")
                print(f"添加时间: {result['add_time']}")
                if result['txt_content']:
                    print(f"文本预览: {result['txt_content'][:200]}...")
        else:
            print("未找到记录")
        return
    
    if args.db_questions:
        print("=== 查询新格式数据库 ===")
        results = analyzer.get_questions_from_database()
        print(f"总题目数: {len(results)}")
        for result in results[:10]:  # 显示前10条
            print(f"  {result['file_path']} - {result['question_id']} -> {result['question_type']} ({result['add_time']})")
        if len(results) > 10:
            print(f"  ... 还有 {len(results) - 10} 条记录")
        return
    
    if args.db_file:
        print(f"=== 查询文件: {args.db_file} ===")
        results = analyzer.get_questions_from_database(args.db_file)
        if results:
            for result in results:
                print(f"题目ID: {result['question_id']}")
                print(f"题型: {result['question_type']}")
                print(f"置信度: {result['confidence']}")
                print(f"题干: {result['content'][:200]}...")
                if result['options']:
                    print(f"选项: {result['options']}")
                print(f"添加时间: {result['add_time']}")
                print("---")
        else:
            print("未找到记录")
        return
    
    # 检查是否提供了输入路径
    if not args.input:
        print("请提供输入文件或目录路径，或使用数据库查询选项")
        print("使用 --help 查看所有选项")
        sys.exit(1)
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # 分析单个文件
        print(f"分析文件: {input_path}")
        result = analyzer.analyze_file(input_path, force_reanalyze=args.force_reanalyze, skip_cached=args.skip_cached)
        
        if "skipped" in result:
            print(f"跳过: {result['reason']}")
        elif "error" not in result:
            if "questions" in result:
                # 多题目文件
                print(f"题目数量: {result['question_count']}")
                print(f"来源: {result['source']}")
                print()
                for i, question in enumerate(result['questions'], 1):
                    print(f"题目 {i}:")
                    print(f"  ID: {question['question_id']}")
                    print(f"  题型: {question['question_type']}")
                    print(f"  置信度: {question['confidence']:.2f}")
                    print(f"  题干预览: {question['text_preview']}")
                    print(f"  选项: {question['options']}")
                    print()
            else:
                # 单题目文件
                print(f"题型: {result['question_type']}")
                print(f"置信度: {result['confidence']:.2f}")
                print(f"文本预览: {result['text_preview']}")
        else:
            print(f"错误: {result['error']}")
    
    elif input_path.is_dir():
        # 批量分析目录
        print(f"分析目录: {input_path}")
        results = analyzer.batch_analyze(input_path, args.pattern, args.max_files, args.force_reanalyze, args.batch_size, args.max_workers, args.skip_cached)
        
        # 保存结果
        analyzer.save_results(results, args.output)
        
        # 生成摘要
        summary = analyzer.generate_summary(results)
        print(summary)
        
        # 保存摘要
        with open("question_types_summary.txt", 'w', encoding='utf-8') as f:
            f.write(summary)
        print("摘要已保存到: question_types_summary.txt")
        
        # 显示数据库统计
        print("\n=== 数据库统计 ===")
        db_summary = analyzer.generate_database_summary()
        print(db_summary)
    
    else:
        print(f"路径不存在: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
