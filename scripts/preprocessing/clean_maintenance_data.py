#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据清洗与标准化脚本

该脚本用于处理原始Excel维护数据，执行以下操作：
1. 标准化产品型号（统一为'DCS-50FB3+'或'DCS-50LD'）
2. 清洗文本字段（信息描述和现场处理方案）
3. 解析问题分类的层级结构
4. 为RAG应用准备结构化数据
"""

import re
import pandas as pd
import numpy as np
import unicodedata
from pathlib import Path

# 输入和输出文件路径
INPUT_FILE = Path("/Users/Apple/workspace/kotaemon/scripts/preprocessing/data/collection_raw.xlsx")
OUTPUT_FILE = Path("/Users/Apple/workspace/kotaemon/scripts/preprocessing/data/collection_cleaned.xlsx")

# 产品型号标准化映射
def standardize_product_model(model):
    """
    将各种产品型号变体标准化为'DCS-50FB3+'或'DCS-50LD'
    
    Args:
        model: 原始产品型号字符串
        
    Returns:
        标准化后的产品型号
    """
    if not isinstance(model, str):
        return "未知型号"
    
    # 转换为大写以便统一处理
    model = model.upper()
    
    # 移除所有空白字符
    model = re.sub(r'\s+', '', model)
    
    # DCS-50FB3+及其变体
    if re.search(r'(DCS[-\s]*50\s*FB\s*3|50\s*FB\s*3|FB\s*3)', model):
        return "DCS-50FB3+"
    
    # DCS-50LD及其变体
    elif re.search(r'(DCS[-\s]*50\s*LD|50\s*LD)', model):
        return "DCS-50LD"
    
    # 默认返回DCS-50FB3+（如果无法确定）
    else:
        print(f"警告: 无法识别的产品型号 '{model}'，默认设置为'DCS-50FB3+'")
        return "DCS-50FB3+"

# 文本清洗函数
def clean_text(text):
    """
    清洗文本，包括：
    - 全角转半角
    - 统一换行符
    - 移除多余空格
    - 移除特殊字符
    
    Args:
        text: 原始文本
        
    Returns:
        清洗后的文本
    """
    if not isinstance(text, str):
        return ""
    
    # 全角转半角
    text = unicodedata.normalize('NFKC', text)
    
    # 统一换行符
    text = re.sub(r'\r\n|\r', '\n', text)
    
    # 移除多余空格
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'^\s+|\s+$', '', text)
    
    # 替换常见的无意义符号组合
    text = re.sub(r'[\*]+', '*', text)
    text = re.sub(r'[\-]+', '-', text)
    text = re.sub(r'[\~]+', '~', text)
    
    # 保留有意义的标点符号
    text = re.sub(r'[^\w\s\n.,;:!?()\[\]{}"\'\-+*/=<>%&@#$~\\]', '', text)
    
    return text

# 解析问题分类层级结构
def parse_problem_category(category):
    """
    解析问题分类的层级结构
    
    Args:
        category: 原始问题分类字符串（如"电气系统故障/低压电器故障"）
        
    Returns:
        包含层级信息的字典
    """
    if not isinstance(category, str):
        return {"level_1": "未分类", "level_2": "未分类"}
    
    # 清洗分类文本
    category = clean_text(category)
    
    # 按分隔符拆分层级
    levels = category.split('/')
    
    result = {}
    for i, level in enumerate(levels, 1):
        result[f"level_{i}"] = level.strip()
    
    # 确保至少有两个层级
    if "level_1" not in result:
        result["level_1"] = "未分类"
    if "level_2" not in result:
        result["level_2"] = "未分类"
    
    return result

def main():
    print(f"开始处理文件: {INPUT_FILE}")
    
    # 读取Excel文件
    try:
        df = pd.read_excel(INPUT_FILE)
        print(f"成功读取数据，共 {len(df)} 行")
    except Exception as e:
        print(f"读取文件失败: {e}")
        return
    
    # 确认列名
    expected_columns = ["序号", "产品型号", "问题分类", "信息描述", "现场处理方案"]
    missing_columns = [col for col in expected_columns if col not in df.columns]
    
    if missing_columns:
        print(f"警告: 缺少以下列: {missing_columns}")
        # 尝试根据位置推断列名
        if len(df.columns) >= 5:
            df.columns = expected_columns
            print("已根据位置推断列名")
        else:
            print("无法处理: 列数不足")
            return
    
    # 创建副本以保留原始数据
    cleaned_df = df.copy()
    
    # 1. 标准化产品型号
    print("正在标准化产品型号...")
    cleaned_df["产品型号_标准化"] = cleaned_df["产品型号"].apply(standardize_product_model)
    
    # 2. 清洗文本字段
    print("正在清洗文本字段...")
    cleaned_df["信息描述_清洗"] = cleaned_df["信息描述"].apply(clean_text)
    cleaned_df["现场处理方案_清洗"] = cleaned_df["现场处理方案"].apply(clean_text)
    
    # 3. 解析问题分类
    print("正在解析问题分类...")
    category_df = cleaned_df["问题分类"].apply(parse_problem_category).apply(pd.Series)
    
    # 重命名分类列
    category_df.columns = [f"问题分类_{col}" for col in category_df.columns]
    
    # 合并分类数据
    cleaned_df = pd.concat([cleaned_df, category_df], axis=1)
    
    # 4. 创建元数据列，用于RAG
    print("正在创建元数据...")
    cleaned_df["metadata"] = cleaned_df.apply(
        lambda row: {
            "产品型号": row["产品型号_标准化"],
            "问题分类_主类": row.get("问题分类_level_1", "未分类"),
            "问题分类_子类": row.get("问题分类_level_2", "未分类"),
            "原始序号": row["序号"]
        },
        axis=1
    )
    
    # 保存清洗后的数据
    try:
        # 确保输出目录存在
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # 保存为Excel
        cleaned_df.to_excel(OUTPUT_FILE, index=False)
        print(f"数据清洗完成，已保存到: {OUTPUT_FILE}")
        
        # 额外保存为CSV以便更容易查看
        csv_path = OUTPUT_FILE.with_suffix('.csv')
        cleaned_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f"同时保存为CSV格式: {csv_path}")
        
        # 打印统计信息
        print("\n数据统计:")
        print(f"总记录数: {len(cleaned_df)}")
        print(f"标准化后的产品型号分布:\n{cleaned_df['产品型号_标准化'].value_counts()}")
        print(f"问题分类主类分布:\n{cleaned_df['问题分类_level_1'].value_counts().head(10)}")
        
    except Exception as e:
        print(f"保存文件失败: {e}")

if __name__ == "__main__":
    main()