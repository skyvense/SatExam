#!/usr/bin/env python3
"""
SAT题型识别工具
使用AI分析题目文本，识别SAT考试的题型分类
"""

import argparse
import json
import re
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
            # 检查是否使用OpenRouter
            openrouter_key = os.getenv('OPENROUTER_API_KEY')
            if openrouter_key:
                self.client = openai.OpenAI(
                    api_key=openrouter_key,
                    base_url="https://openrouter.ai/api/v1"
                )
            else:
                self.client = openai.OpenAI(api_key=self.api_key)
        else:
            self.client = None
    
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
{text[:1000]}  # 限制长度避免token过多
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
    
    def analyze_file(self, file_path: Path) -> Dict:
        """
        分析单个文件
        
        Args:
            file_path: 文本文件路径
            
        Returns:
            分析结果字典
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            qtype, confidence, scores = self.classify_question(text)
            
            return {
                "filename": file_path.name,
                "filepath": str(file_path),
                "question_type": qtype,
                "confidence": confidence,
                "scores": scores,
                "text_preview": text[:200] + "..." if len(text) > 200 else text
            }
            
        except Exception as e:
            return {
                "filename": file_path.name,
                "filepath": str(file_path),
                "error": str(e)
            }
    
    def batch_analyze(self, directory: Path, pattern: str = "*.txt", max_files: Optional[int] = None) -> List[Dict]:
        """
        批量分析目录中的文件
        
        Args:
            directory: 目录路径
            pattern: 文件匹配模式
            max_files: 最大处理文件数
            
        Returns:
            分析结果列表
        """
        results = []
        
        if not directory.exists():
            print(f"目录不存在: {directory}")
            return results
        
        txt_files = list(directory.rglob(pattern))
        total_files = len(txt_files)
        
        # 限制文件数量
        if max_files:
            txt_files = txt_files[:max_files]
            print(f"找到 {total_files} 个文本文件，将处理前 {max_files} 个")
        else:
            print(f"找到 {total_files} 个文本文件")
        
        for i, file_path in enumerate(txt_files, 1):
            print(f"[{i}/{len(txt_files)}] 分析: {file_path.name}")
            result = self.analyze_file(file_path)
            results.append(result)
            
            if "error" not in result:
                print(f"  题型: {result['question_type']} (置信度: {result['confidence']:.2f})")
            else:
                print(f"  错误: {result['error']}")
        
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
        
        for result in results:
            if "error" not in result:
                qtype = result["question_type"]
                type_counts[qtype] = type_counts.get(qtype, 0) + 1
                total_files += 1
        
        # 生成报告
        report = f"""
SAT题型分析报告
================

总文件数: {total_files}
成功分析: {len([r for r in results if "error" not in r])}
分析失败: {len([r for r in results if "error" in r])}

题型分布:
"""
        
        for qtype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_files) * 100 if total_files > 0 else 0
            description = self.question_types.get(qtype, {}).get("description", "未知题型")
            report += f"  {qtype}: {count} 题 ({percentage:.1f}%) - {description}\n"
        
        return report


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="SAT题型识别工具")
    parser.add_argument("input", type=str, help="输入文件或目录路径")
    parser.add_argument("--output", "-o", type=str, default="question_types.json", 
                       help="输出文件 (默认: question_types.json)")
    parser.add_argument("--pattern", "-p", type=str, default="*.txt",
                       help="文件匹配模式 (默认: *.txt)")
    parser.add_argument("--api-key", type=str, help="OpenAI或OpenRouter API密钥")
    parser.add_argument("--no-ai", action="store_true", help="禁用AI分析，仅使用规则分析")
    parser.add_argument("--max-files", "-m", type=int, help="最大处理文件数")
    
    args = parser.parse_args()
    
    # 检查API密钥
    api_key = args.api_key or os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
    if not api_key and not args.no_ai:
        print("⚠️  未提供API密钥，将使用规则分析")
        print("请设置环境变量 OPENAI_API_KEY 或 OPENROUTER_API_KEY")
        print("或使用 --api-key 参数提供密钥")
        print("或使用 --no-ai 参数禁用AI分析")
    
    analyzer = QuestionTypeAnalyzer(api_key=api_key if not args.no_ai else None)
    input_path = Path(args.input)
    
    if input_path.is_file():
        # 分析单个文件
        print(f"分析文件: {input_path}")
        result = analyzer.analyze_file(input_path)
        
        if "error" not in result:
            print(f"题型: {result['question_type']}")
            print(f"置信度: {result['confidence']:.2f}")
            print(f"文本预览: {result['text_preview']}")
        else:
            print(f"错误: {result['error']}")
    
    elif input_path.is_dir():
        # 批量分析目录
        print(f"分析目录: {input_path}")
        results = analyzer.batch_analyze(input_path, args.pattern, args.max_files)
        
        # 保存结果
        analyzer.save_results(results, args.output)
        
        # 生成摘要
        summary = analyzer.generate_summary(results)
        print(summary)
        
        # 保存摘要
        with open("question_types_summary.txt", 'w', encoding='utf-8') as f:
            f.write(summary)
        print("摘要已保存到: question_types_summary.txt")
    
    else:
        print(f"路径不存在: {input_path}")
        sys.exit(1)


if __name__ == "__main__":
    main()
