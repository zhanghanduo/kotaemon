"""Signal data loader.

Specialized loader for machine signal data in Excel format.
"""
from pathlib import Path
from typing import Any, List, Optional, Union, Dict

from kotaemon.loaders.maintenance_loader import MaintenanceDataLoader
from kotaemon.base import Document


class SignalDataLoader(MaintenanceDataLoader):
    """Specialized loader for machine signal data.
    
    Parses signal data from Excel files with specific structure for
    equipment IDs, signal types, and processing methods.
    
    This loader is optimized for the format shown in the example with columns for:
    - Equipment/Product ID
    - Signal category
    - Signal description
    - Processing method
    
    Args:
        pandas_config (dict): Options for pandas.read_excel
        entity_columns (list): Columns to treat as entity identifiers
        description_columns (list): Columns containing signal descriptions
        category_columns (list): Columns containing categorization information
    """
    
    def __init__(
        self,
        *args: Any,
        pandas_config: Optional[dict] = None,
        entity_columns: Optional[List[str]] = None,
        description_columns: Optional[List[str]] = None,
        category_columns: Optional[List[str]] = None,
        signal_type_column: Optional[str] = None,
        processing_method_column: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the signal data loader."""
        super().__init__(
            *args, 
            pandas_config=pandas_config,
            entity_columns=entity_columns,
            description_columns=description_columns,
            category_columns=category_columns,
            **kwargs
        )
        self._signal_type_column = signal_type_column
        self._processing_method_column = processing_method_column
    
    def _detect_entity_columns(self, columns: List[str]) -> List[str]:
        """Auto-detect columns that likely contain equipment identifiers."""
        # Based on the screenshot, look for product/equipment ID columns
        entity_keywords = ["序号", "产品型号", "设备", "id", "编号"]
        
        # First column is likely the ID column based on the screenshot
        if columns and len(columns) > 0:
            if any(kw in str(columns[0]).lower() for kw in entity_keywords):
                return [columns[0]]
        
        return [col for col in columns if any(kw in str(col).lower() for kw in entity_keywords)]
    
    def _detect_signal_type_column(self, columns: List[str]) -> Optional[str]:
        """Auto-detect column that contains signal type information."""
        if self._signal_type_column:
            return self._signal_type_column
            
        signal_keywords = ["信号分类", "信号类型", "signal type", "类别"]
        for col in columns:
            if any(kw in str(col).lower() for kw in signal_keywords):
                return col
        return None
    
    def _detect_processing_method_column(self, columns: List[str]) -> Optional[str]:
        """Auto-detect column that contains processing method information."""
        if self._processing_method_column:
            return self._processing_method_column
            
        method_keywords = ["处理方案", "processing method", "处理"]
        for col in columns:
            if any(kw in str(col).lower() for kw in method_keywords):
                return col
        return None
    
    def load_data(
        self,
        file: Path,
        include_sheetname: bool = True,
        sheet_name: Optional[Union[str, int, list]] = None,
        extra_info: Optional[dict] = None,
        **kwargs,
    ) -> List[Document]:
        """Load signal data from Excel file.
        
        Creates structured documents with metadata suitable for both
        vector stores and knowledge graph integration, with special handling
        for signal type and processing method columns.
        
        Args:
            file (Path): Path to the Excel file
            include_sheetname (bool): Whether to include sheet name in output
            sheet_name (Union[str, int, list, None]): Specific sheet(s) to read
            extra_info (dict): Additional metadata
            
        Returns:
            List[Document]: Documents with structured signal data
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
            
            # Auto-detect columns
            columns = df.columns.tolist()
            entity_cols = self._entity_columns or self._detect_entity_columns(columns)
            desc_cols = self._description_columns or self._detect_description_columns(columns)
            cat_cols = self._category_columns or self._detect_category_columns(columns)
            
            # Detect signal-specific columns
            signal_type_col = self._detect_signal_type_column(columns)
            processing_method_col = self._detect_processing_method_column(columns)
            
            # Process each row as a separate document
            for row_idx, row in df.iterrows():
                row_dict = row.to_dict()
                
                # Create entity identifier
                entity_id = "_".join([str(row_dict.get(col, "")).strip() for col in entity_cols if str(row_dict.get(col, "")).strip()])
                if not entity_id and len(entity_cols) == 0 and row_idx is not None:
                    # Fallback to row index if no entity columns detected
                    entity_id = f"row_{row_idx}"
                
                # Extract descriptions
                descriptions = "\n".join([f"{col}: {str(row_dict.get(col, '')).strip()}" for col in desc_cols if str(row_dict.get(col, '')).strip()])
                
                # Extract signal type and processing method
                signal_type = str(row_dict.get(signal_type_col, "")).strip() if signal_type_col else ""
                processing_method = str(row_dict.get(processing_method_col, "")).strip() if processing_method_col else ""
                
                # Create structured categories dictionary
                categories = {col: str(row_dict.get(col, "")).strip() for col in cat_cols}
                if signal_type:
                    categories["signal_type"] = signal_type
                if processing_method:
                    categories["processing_method"] = processing_method
                
                # Create document content with structured format based on the screenshot
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
                    "entity_type": "signal_record",
                    "source_file": str(file),
                }
                
                # Add signal-specific metadata
                if signal_type:
                    metadata["signal_type"] = signal_type
                if processing_method:
                    metadata["processing_method"] = processing_method
                
                # Add any extra info
                metadata.update(extra_info)
                
                output.append(Document(text=content, metadata=metadata))
        
        return output