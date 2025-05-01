"""Maintenance data index for equipment maintenance records."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import gradio as gr
import pandas as pd

from kotaemon.base import Document
from kotaemon.indices.base import BaseIndex
from kotaemon.loaders.maintenance_loader import MaintenanceDataLoader
from kotaemon.indices.qa.citation_qa import AnswerWithContextPipeline


class MaintenanceIndex(BaseIndex):
    """Index for equipment maintenance data.
    
    Specialized index for handling maintenance records with support for
    both vector search and knowledge graph queries.
    """
    
    def __init__(
        self,
        name: str = "设备维护数据",
        id: str = "maintenance",
        description: str = "设备维护记录和故障分析",
        **kwargs
    ):
        """Initialize the maintenance index."""
        super().__init__(
            name=name,
            id=id,
            description=description,
            **kwargs
        )
        self.loader = MaintenanceDataLoader()
        self.qa_pipeline = AnswerWithContextPipeline(
            enable_citation=True,
            enable_citation_viz=True
        )
    
    def load_data(
        self, 
        file_path: Union[str, Path], 
        entity_columns: Optional[List[str]] = None,
        description_columns: Optional[List[str]] = None,
        category_columns: Optional[List[str]] = None,
        **kwargs
    ) -> List[Document]:
        """Load maintenance data from Excel file.
        
        Args:
            file_path: Path to the Excel file
            entity_columns: Columns to treat as entity identifiers
            description_columns: Columns containing maintenance descriptions
            category_columns: Columns containing categorization information
            
        Returns:
            List of documents containing maintenance records
        """
        # Configure loader with column specifications if provided
        if entity_columns:
            self.loader._entity_columns = entity_columns
        if description_columns:
            self.loader._description_columns = description_columns
        if category_columns:
            self.loader._category_columns = category_columns
            
        # Load documents
        documents = self.loader.load_data(file_path)
        
        # Add documents to the index
        self.add_documents(documents)
        
        return documents
    
    def get_index_page_ui(self):
        """Create the UI for the maintenance index page."""
        with gr.Blocks() as page:
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown(f"# {self.name}")
                    gr.Markdown(self.description)
                    
            with gr.Row():
                with gr.Column():
                    file_upload = gr.File(
                        label="上传维护数据Excel文件",
                        file_types=[".xlsx", ".xls"],
                    )
                    
                    with gr.Row():
                        entity_cols = gr.Textbox(
                            label="设备标识列（逗号分隔）", 
                            placeholder="例如：产品编号,设备号"
                        )
                        desc_cols = gr.Textbox(
                            label="描述信息列（逗号分隔）", 
                            placeholder="例如：信息描述,故障处理方法"
                        )
                        cat_cols = gr.Textbox(
                            label="分类信息列（逗号分隔）", 
                            placeholder="例如：问题分类"
                        )
                    
                    upload_btn = gr.Button("处理并索引数据")
                    upload_status = gr.Markdown("准备就绪")
            
            with gr.Row():
                with gr.Column():
                    query_input = gr.Textbox(
                        label="输入查询问题", 
                        placeholder="例如：DCS-50FE+设备有什么常见故障？"
                    )
                    query_btn = gr.Button("查询")
                    
                    with gr.Row():
                        with gr.Column(scale=2):
                            answer_output = gr.Markdown(label="回答")
                        with gr.Column(scale=1):
                            sources_output = gr.Dataframe(
                                label="参考来源",
                                headers=["设备", "描述", "来源"]
                            )
            
            def process_file(file, entity_str, desc_str, cat_str):
                if not file:
                    return "请先上传文件"
                
                entity_columns = [c.strip() for c in entity_str.split(",")] if entity_str else None
                desc_columns = [c.strip() for c in desc_str.split(",")] if desc_str else None
                cat_columns = [c.strip() for c in cat_str.split(",")] if cat_str else None
                
                try:
                    docs = self.load_data(
                        file.name,
                        entity_columns=entity_columns,
                        description_columns=desc_columns,
                        category_columns=cat_columns
                    )
                    return f"成功处理 {len(docs)} 条维护记录"
                except Exception as e:
                    return f"处理失败: {str(e)}"
            
            def query_index(question):
                if not question:
                    return "请输入查询问题", []
                
                # Retrieve relevant documents
                retrieved_docs = self.retrieve(question, top_k=5)
                if not retrieved_docs:
                    return "未找到相关信息", []
                
                # Format evidence for QA
                evidence = "\n\n".join([doc.text for doc in retrieved_docs])
                
                # Generate answer with citations
                answer = self.qa_pipeline.invoke(question, evidence)
                
                # Extract sources for display
                sources = []
                if answer.metadata.get("citation"):
                    for doc in retrieved_docs:
                        entity_id = doc.metadata.get("entity_id", "未知设备")
                        desc = doc.text[:100] + "..." if len(doc.text) > 100 else doc.text
                        source = doc.metadata.get("source_file", "未知来源")
                        sources.append([entity_id, desc, source])
                
                return answer.text, sources
            
            upload_btn.click(
                process_file,
                inputs=[file_upload, entity_cols, desc_cols, cat_cols],
                outputs=upload_status
            )
            
            query_btn.click(
                query_index,
                inputs=query_input,
                outputs=[answer_output, sources_output]
            )
            
        return page
