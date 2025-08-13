#!/usr/bin/env python3
"""
SAT PDF Parser
用于解析SAT考试PDF文件的工具
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import PyPDF2
import pdfplumber
import pandas as pd

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('parser.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class SATPDFParser:
    """SAT PDF文件解析器"""
    
    def __init__(self, data_dir: str = "../../data/income/SAT真题"):
        """
        初始化解析器
        
        Args:
            data_dir: 数据目录路径
        """
        self.data_dir = Path(data_dir)
        self.results = {}
        
    def scan_pdf_files(self) -> List[Path]:
        """
        扫描数据目录中的所有PDF文件
        
        Returns:
            PDF文件路径列表
        """
        pdf_files = []
        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(Path(root) / file)
        
        logger.info(f"找到 {len(pdf_files)} 个PDF文件")
        return pdf_files
    
    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """
        从PDF文件中提取文本
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            提取的文本内容
        """
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            logger.info(f"成功提取文本: {pdf_path.name}")
            return text
            
        except Exception as e:
            logger.error(f"提取文本失败 {pdf_path.name}: {str(e)}")
            return ""
    
    def get_pdf_info(self, pdf_path: Path) -> Dict:
        """
        获取PDF文件的基本信息
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            PDF文件信息字典
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                info = {
                    'filename': pdf_path.name,
                    'filepath': str(pdf_path),
                    'pages': len(pdf_reader.pages),
                    'size_mb': round(pdf_path.stat().st_size / (1024 * 1024), 2)
                }
                
                # 尝试获取PDF元数据
                if pdf_reader.metadata:
                    info['title'] = pdf_reader.metadata.get('/Title', '')
                    info['author'] = pdf_reader.metadata.get('/Author', '')
                    info['subject'] = pdf_reader.metadata.get('/Subject', '')
                
                return info
                
        except Exception as e:
            logger.error(f"获取PDF信息失败 {pdf_path.name}: {str(e)}")
            return {'filename': pdf_path.name, 'error': str(e)}
    
    def analyze_sat_content(self, text: str) -> Dict:
        """
        分析SAT考试内容
        
        Args:
            text: 提取的文本内容
            
        Returns:
            分析结果字典
        """
        analysis = {
            'total_words': len(text.split()),
            'total_chars': len(text),
            'sections': {},
            'question_count': 0,
            'keywords': []
        }
        
        # 检测常见SAT部分
        sections = {
            'reading': ['reading', 'passage', 'comprehension'],
            'writing': ['writing', 'grammar', 'language'],
            'math': ['math', 'mathematics', 'algebra', 'geometry', 'calculus'],
            'essay': ['essay', 'writing sample']
        }
        
        text_lower = text.lower()
        
        for section, keywords in sections.items():
            count = sum(text_lower.count(keyword) for keyword in keywords)
            if count > 0:
                analysis['sections'][section] = count
        
        # 统计题目数量（简单估算）
        question_patterns = [
            r'\d+\.',  # 数字后跟点
            r'question \d+',
            r'problem \d+'
        ]
        
        import re
        for pattern in question_patterns:
            matches = re.findall(pattern, text_lower)
            analysis['question_count'] += len(matches)
        
        # 提取关键词
        common_words = ['sat', 'test', 'exam', 'question', 'answer', 'passage', 'reading', 'writing', 'math']
        for word in common_words:
            if word in text_lower:
                analysis['keywords'].append(word)
        
        return analysis
    
    def process_all_pdfs(self) -> Dict:
        """
        处理所有PDF文件
        
        Returns:
            处理结果字典
        """
        pdf_files = self.scan_pdf_files()
        
        for pdf_path in pdf_files:
            logger.info(f"处理文件: {pdf_path.name}")
            
            # 获取PDF信息
            pdf_info = self.get_pdf_info(pdf_path)
            
            # 提取文本
            text = self.extract_text_from_pdf(pdf_path)
            
            # 分析内容
            if text:
                analysis = self.analyze_sat_content(text)
                pdf_info['analysis'] = analysis
                pdf_info['text_preview'] = text[:500] + "..." if len(text) > 500 else text
            else:
                pdf_info['analysis'] = {}
                pdf_info['text_preview'] = ""
            
            self.results[pdf_path.name] = pdf_info
        
        return self.results
    
    def save_results(self, output_file: str = "sat_analysis_results.json"):
        """
        保存分析结果到JSON文件
        
        Args:
            output_file: 输出文件名
        """
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            logger.info(f"结果已保存到: {output_file}")
        except Exception as e:
            logger.error(f"保存结果失败: {str(e)}")
    
    def generate_summary_report(self) -> str:
        """
        生成摘要报告
        
        Returns:
            摘要报告文本
        """
        if not self.results:
            return "没有处理结果"
        
        total_files = len(self.results)
        total_pages = sum(info.get('pages', 0) for info in self.results.values())
        total_size = sum(info.get('size_mb', 0) for info in self.results.values())
        
        report = f"""
SAT PDF 分析报告
================

总文件数: {total_files}
总页数: {total_pages}
总大小: {total_size:.2f} MB

文件列表:
"""
        
        for filename, info in self.results.items():
            pages = info.get('pages', 0)
            size = info.get('size_mb', 0)
            report += f"- {filename}: {pages}页, {size}MB\n"
        
        return report


def main():
    """主函数"""
    parser = SATPDFParser()
    
    print("开始处理SAT PDF文件...")
    results = parser.process_all_pdfs()
    
    if results:
        # 保存结果
        parser.save_results()
        
        # 生成报告
        report = parser.generate_summary_report()
        print(report)
        
        # 保存报告
        with open("sat_analysis_report.txt", 'w', encoding='utf-8') as f:
            f.write(report)
        
        print("处理完成！")
    else:
        print("没有找到PDF文件或处理失败")


if __name__ == "__main__":
    main()
