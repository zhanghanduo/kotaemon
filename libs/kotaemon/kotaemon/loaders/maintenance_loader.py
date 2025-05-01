"""Maintenance data loader.

Specialized loader for machine maintenance data in Excel format.
"""
from pathlib import Path
from typing import Any, List, Optional, Union, Dict

from llama_index.core.readers.base import BaseReader

from kotaemon.base import Document
from kotaemon.loaders.excel_loader import ExcelReader


class MaintenanceDataLoader(ExcelReader):
    """Specialized loader for machine maintenance data.
    
    Parses maintenance data from Excel files and structures it for 
    vector stores and knowledge graphs.
    
    Args:
        pandas_config (dict): Options for pandas.read_excel
        entity_columns (list): Columns to treat as entity identifiers
        description_columns (list): Columns containing maintenance descriptions
        category_columns (list): Columns containing categorization information
    """
    
    def __init__(
        self,
        *args: Any,
        pandas_config: Optional[dict] = None,
        entity_columns: Optional[List[str]] = None,
        description_columns: Optional[List[str]] = None,
        category_columns: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the maintenance data loader."""
        super().__init__(*args, pandas_config=pandas_config, **kwargs)
        self._entity_columns = entity_columns or []
        self._description_columns = description_columns or []
        self._category_columns = category_columns or []
    
    def load_data(
        self,
        file: Path,
        include_sheetname: bool = True,
        sheet_name: Optional[Union[str, int, list]] = None,
        extra_info: Optional[dict] = None,
        chunk_by_row: bool = True,
        **kwargs,
    ) -> List[Document]:
        """Load maintenance data from Excel file.
        
        Creates structured documents with metadata suitable for both
        vector stores and knowledge graph integration.
        
        Args:
            file (Path): Path to the Excel file
            include_sheetname (bool): Whether to include sheet name in output
            sheet_name (Union[str, int, list, None]): Specific sheet(s) to read
            extra_info (dict): Additional metadata
            
        Returns:
            List[Document]: Documents with structured maintenance data
        """
        import pandas as pd
        
        file = Path(file)
        extra_info = extra_info or {}
        
        if sheet_name is not None:
            sheet_name = (
                [sheet_name] if not isinstance(sheet_name, list) else sheet_name
            )
        
        dfs = pd.read_excel(file, sheet_name=sheet_name, **self._pandas_config)
        sheet_names = dfs.keys()
        output = []
        
        for idx, key in enumerate(sheet_names):
            df = dfs[key]
            df = df.dropna(axis=0, how="all")
            df = df.dropna(axis=1, how="all")
            df = df.astype("object")
            df.fillna("", inplace=True)
            
            # Auto-detect entity, description and category columns if not provided
            columns = df.columns.tolist()
            entity_cols = self._entity_columns or self._detect_entity_columns(columns)
            desc_cols = self._description_columns or self._detect_description_columns(columns)
            cat_cols = self._category_columns or self._detect_category_columns(columns)
            
            # Process each row as a separate document
            for row_idx, row in df.iterrows():
                row_dict = row.to_dict()
                
                # Create entity identifier
                entity_id = "_".join([str(row_dict.get(col, "")).strip() for col in entity_cols if str(row_dict.get(col, "")).strip()])
                if not entity_id and len(entity_cols) == 0 and row_idx is not None:
                    # Fallback to row index if no entity columns detected
                    entity_id = f"row_{row_idx}"
                
                # Extract descriptions and categories
                descriptions = "\n".join([f"{col}: {str(row_dict.get(col, '')).strip()}" for col in desc_cols if str(row_dict.get(col, '')).strip()])
                
                # Extract signal type and processing method (based on screenshot)
                signal_type = ""
                processing_method = ""
                
                # Look for signal type and processing method columns based on the screenshot
                for col in columns:
                    col_lower = str(col).lower()
                    if any(kw in col_lower for kw in ["信号", "signal", "类型"]):
                        signal_type = str(row_dict.get(col, "")).strip()
                    elif any(kw in col_lower for kw in ["处理", "方案", "processing", "method"]):
                        processing_method = str(row_dict.get(col, "")).strip()
                
                # Create structured categories dictionary
                categories = {col: str(row_dict.get(col, "")).strip() for col in cat_cols}
                if signal_type:
                    categories["signal_type"] = signal_type
                if processing_method:
                    categories["processing_method"] = processing_method
                
                # Create document content with more structured format
                content = f"Equipment ID: {entity_id}\n"
                if signal_type:
                    content += f"Signal Type: {signal_type}\n"
                if processing_method:
                    content += f"Processing Method: {processing_method}\n"
                content += f"Description:\n{descriptions}"
                
                # Create metadata for vector store and graph database
                metadata = {
                    "entity_id": entity_id,
                    "sheet_name": key,
                    "row_index": row_idx,
                    "categories": categories,
                    "entity_type": "maintenance_record",
                    "source_file": str(file),
                    **extra_info
                }
                
                output.append(Document(text=content, metadata=metadata))
        
        return output
    
    def _detect_entity_columns(self, columns: List[str]) -> List[str]:
        """Auto-detect columns that likely contain entity identifiers."""
        entity_keywords = ["id", "编号", "号", "设备", "产品", "型号", "code", "number", "序号", "产品型号"]
        # Based on the screenshot, the first column appears to be a product/equipment ID
        if columns and len(columns) > 0:
            # If the first column looks like an ID column, prioritize it
            if any(kw in str(columns[0]).lower() for kw in entity_keywords):
                return [columns[0]]
        return [col for col in columns if any(kw in str(col).lower() for kw in entity_keywords)]
    
    def _detect_description_columns(self, columns: List[str]) -> List[str]:
        """Auto-detect columns that likely contain descriptions."""
        desc_keywords = ["描述", "说明", "信息", "内容", "desc", "description", "info", "detail", "信息描述"]
        # From the screenshot, the signal description column appears to be important
        detected = [col for col in columns if any(kw in str(col).lower() for kw in desc_keywords)]
        # If no description columns found, try to use columns with longer text content
        if not detected and len(columns) > 2:
            # The screenshot shows the rightmost column contains detailed descriptions
            return [columns[-1]]
        return detected
    
    def _detect_category_columns(self, columns: List[str]) -> List[str]:
        """Auto-detect columns that likely contain categorization."""
        cat_keywords = ["类别", "类型", "分类", "category", "type", "class", "分类", "处理方案"]
        # From the screenshot, there appears to be a category/classification column
        return [col for col in columns if any(kw in str(col).lower() for kw in cat_keywords)]