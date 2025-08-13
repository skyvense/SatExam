#!/usr/bin/env python3
"""
SAT PDF Parser 使用示例
"""

from pdf_parser import SATPDFParser
import json

def example_basic_usage():
    """基本使用示例"""
    print("=== SAT PDF Parser 基本使用示例 ===")
    
    # 创建解析器实例
    parser = SATPDFParser(data_dir="../data")
    
    # 扫描PDF文件
    pdf_files = parser.scan_pdf_files()
    print(f"找到 {len(pdf_files)} 个PDF文件")
    
    # 处理前几个文件作为示例
    for i, pdf_path in enumerate(pdf_files[:3]):  # 只处理前3个文件
        print(f"\n处理文件 {i+1}: {pdf_path.name}")
        
        # 获取PDF信息
        info = parser.get_pdf_info(pdf_path)
        print(f"  页数: {info.get('pages', 'N/A')}")
        print(f"  大小: {info.get('size_mb', 'N/A')} MB")
        
        # 提取文本（只提取前1000字符作为预览）
        text = parser.extract_text_from_pdf(pdf_path)
        if text:
            preview = text[:1000] + "..." if len(text) > 1000 else text
            print(f"  文本预览: {preview[:200]}...")
        else:
            print("  无法提取文本")

def example_full_analysis():
    """完整分析示例"""
    print("\n=== 完整分析示例 ===")
    
    # 创建解析器并处理所有文件
    parser = SATPDFParser(data_dir="../data")
    results = parser.process_all_pdfs()
    
    if results:
        # 保存结果
        parser.save_results("example_results.json")
        
        # 生成报告
        report = parser.generate_summary_report()
        print(report)
        
        # 显示详细分析
        print("\n详细分析:")
        for filename, info in results.items():
            analysis = info.get('analysis', {})
            print(f"\n{filename}:")
            print(f"  总字数: {analysis.get('total_words', 0)}")
            print(f"  题目数量: {analysis.get('question_count', 0)}")
            print(f"  检测到的部分: {list(analysis.get('sections', {}).keys())}")
            print(f"  关键词: {analysis.get('keywords', [])}")

def example_custom_analysis():
    """自定义分析示例"""
    print("\n=== 自定义分析示例 ===")
    
    parser = SATPDFParser(data_dir="../data")
    pdf_files = parser.scan_pdf_files()
    
    if pdf_files:
        # 选择一个文件进行详细分析
        target_file = pdf_files[0]
        print(f"分析文件: {target_file.name}")
        
        # 提取文本
        text = parser.extract_text_from_pdf(target_file)
        
        if text:
            # 自定义分析
            analysis = parser.analyze_sat_content(text)
            
            print(f"文本统计:")
            print(f"  总字符数: {analysis['total_chars']}")
            print(f"  总单词数: {analysis['total_words']}")
            print(f"  估算题目数: {analysis['question_count']}")
            
            print(f"\n部分分析:")
            for section, count in analysis['sections'].items():
                print(f"  {section}: {count} 次提及")
            
            print(f"\n关键词: {', '.join(analysis['keywords'])}")

if __name__ == "__main__":
    # 运行示例
    example_basic_usage()
    example_full_analysis()
    example_custom_analysis()
