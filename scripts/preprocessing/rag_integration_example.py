#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
维护数据RAG集成示例

该脚本展示如何将清洗后的维护数据集成到kotaemon库中，
用于构建基于知识图谱的RAG应用。
"""

import os
from pathlib import Path
from typing import List, Dict, Any

# 导入数据加载器
# from load_maintenance_data import MaintenanceDataRAGLoader # Remove this line

# 导入kotaemon库组件
from kotaemon.base import Document
# Add MaintenanceDataLoader import
from kotaemon.loaders import MaintenanceDataLoader, MaintenanceGraphLoader

# Remove convert_to_kotaemon_documents function
def convert_to_kotaemon_documents(documents: List[Dict[str, Any]]) -> List[Document]:
    """
    将加载器文档转换为kotaemon Document对象
    
    Args:
        documents: 从MaintenanceDataRAGLoader获取的文档列表
        
    Returns:
        kotaemon Document对象列表
    """
    kotaemon_docs = []
    
    for doc in documents:
        text = doc["text"]
        metadata = doc["metadata"]
        
        # 创建kotaemon Document对象
        kotaemon_doc = Document(
            text=text,
            metadata={
                "entity_id": f"{metadata['产品型号']}_{metadata['原始序号']}",
                "entity_type": "maintenance_record",
                "categories": {
                    "product_model": metadata["产品型号"],
                    "problem_category_main": metadata["问题分类_主类"],
                    "problem_category_sub": metadata["问题分类_子类"]
                }
            }
        )
        
        kotaemon_docs.append(kotaemon_doc)
    
    return kotaemon_docs

def create_knowledge_graph(kotaemon_docs: List[Document]) -> List[Document]:
    """
    使用MaintenanceGraphLoader创建知识图谱文档
    
    Args:
        kotaemon_docs: kotaemon Document对象列表
        
    Returns:
        知识图谱文档列表
    """
    # 创建一个临时的关系映射 (可以保留或根据MaintenanceGraphLoader的实现调整)
    relationship_mapping = {
        "product_model": "HAS_PRODUCT_MODEL",
        "problem_category_main": "HAS_PROBLEM_CATEGORY",
        "problem_category_sub": "HAS_PROBLEM_SUBCATEGORY"
    }
    
    # 初始化图谱加载器
    graph_loader = MaintenanceGraphLoader(
        relationship_mapping=relationship_mapping
        # 可能需要根据MaintenanceGraphLoader的__init__调整参数
    )
    
    # 使用GraphLoader加载文档
    graph_documents = graph_loader.load(kotaemon_docs) # Pass documents directly
    
    # Remove manual extraction loop
    graph_documents = []
    
    for doc in kotaemon_docs:
        # 创建实体文档
        entity_doc = Document(
            text=doc.text,
            metadata={
                **doc.metadata,
                "node_type": "entity",
                "entity_type": "equipment",
            }
        )
        graph_documents.append(entity_doc)
        
        # 提取关系
        entity_id = doc.metadata.get("entity_id", "")
        categories = doc.metadata.get("categories", {})
        
        # 为每个类别创建关系文档
        for cat_key, cat_value in categories.items():
            if cat_value:
                rel_type = relationship_mapping.get(cat_key, f"HAS_{cat_key.upper()}")
                
                # 创建关系文档
                rel_doc = Document(
                    text=f"{entity_id} {rel_type} {cat_value}",
                    metadata={
                        "node_type": "relationship",
                        "relationship_type": rel_type,
                        "source_id": entity_id,
                        "target_id": cat_value,
                        "properties": {"category": cat_key}
                    }
                )
                graph_documents.append(rel_doc)
    
    return graph_documents

def main():
    # 指定数据路径
    # 确保 data 目录和 collection_cleaned.xlsx 文件存在于 scripts/preprocessing/ 目录下
    data_path = Path(__file__).parent / "data" / "collection_cleaned.xlsx"
    if not data_path.exists():
        print(f"错误：数据文件未找到于 {data_path}")
        print("请确保 'data' 文件夹和 'collection_cleaned.xlsx' 文件位于 'scripts/preprocessing' 目录下。")
        return

    print("使用 MaintenanceDataLoader 加载清洗后的维护数据...")
    # Use MaintenanceDataLoader
    loader = MaintenanceDataLoader(file_path=str(data_path)) 
    # Load directly into kotaemon_docs
    kotaemon_docs = loader.load() 
    print(f"加载了 {len(kotaemon_docs)} 个Document对象")
    
    # Remove conversion step
    print("\n转换为kotaemon Document对象...")
    kotaemon_docs = convert_to_kotaemon_documents(documents)
    print(f"转换了 {len(kotaemon_docs)} 个Document对象")
    
    print("\n使用 MaintenanceGraphLoader 创建知识图谱文档...")
    # Pass kotaemon_docs directly
    graph_docs = create_knowledge_graph(kotaemon_docs) 
    print(f"创建了 {len(graph_docs)} 个知识图谱文档")
    
    # 打印示例 (保持不变)
    print("\n实体文档示例:")
    entity_docs = [doc for doc in graph_docs if doc.metadata.get("node_type") == "entity"]
    if entity_docs:
        print(f"文本: {entity_docs[0].text[:100]}...")
        print(f"元数据: {entity_docs[0].metadata}")
    
    print("\n关系文档示例:")
    rel_docs = [doc for doc in graph_docs if doc.metadata.get("node_type") == "relationship"]
    if rel_docs:
        print(f"文本: {rel_docs[0].text}")
        print(f"元数据: {rel_docs[0].metadata}")
    
    print("\n这些文档可以用于:")
    print("1. 构建向量存储，用于语义搜索")
    print("2. 构建知识图谱，用于结构化查询")
    print("3. 结合向量存储和知识图谱，实现混合检索策略")

if __name__ == "__main__":
    main()