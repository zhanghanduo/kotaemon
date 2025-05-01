"""Maintenance Graph Loader.

Specialized loader for converting maintenance data into knowledge graph format.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Tuple

from kotaemon.loaders.signal_loader import SignalDataLoader
from kotaemon.base import Document


class MaintenanceGraphLoader(SignalDataLoader):
    """Specialized loader for creating knowledge graph data from maintenance records.
    
    Extends the SignalDataLoader to create structured data suitable for
    knowledge graph construction, with explicit entity and relationship extraction.
    
    This loader is optimized for the format shown in the example with columns for:
    - Equipment/Product ID (entities)
    - Signal category (relationships)
    - Signal description (properties)
    - Processing method (relationships)
    
    Args:
        pandas_config (dict): Options for pandas.read_excel
        entity_columns (list): Columns to treat as entity identifiers
        description_columns (list): Columns containing signal descriptions
        category_columns (list): Columns containing categorization information
        signal_type_column (str): Column containing signal type information
        processing_method_column (str): Column containing processing method information
        relationship_mapping (dict): Custom mapping for relationship types
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
        relationship_mapping: Optional[Dict[str, str]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the maintenance graph loader."""
        super().__init__(
            *args, 
            pandas_config=pandas_config,
            entity_columns=entity_columns,
            description_columns=description_columns,
            category_columns=category_columns,
            signal_type_column=signal_type_column,
            processing_method_column=processing_method_column,
            **kwargs
        )
        self._relationship_mapping = relationship_mapping or {}
    
    def load_data(
        self,
        file: Path,
        include_sheetname: bool = True,
        sheet_name: Optional[Union[str, int, list]] = None,
        extra_info: Optional[dict] = None,
        extract_relationships: bool = True,
        **kwargs,
    ) -> List[Document]:
        """Load maintenance data and extract graph relationships.
        
        Creates structured documents with explicit entity and relationship
        information suitable for knowledge graph construction.
        
        Args:
            file (Path): Path to the Excel file
            include_sheetname (bool): Whether to include sheet name in output
            sheet_name (Union[str, int, list, None]): Specific sheet(s) to read
            extra_info (dict): Additional metadata
            extract_relationships (bool): Whether to extract relationships
            
        Returns:
            List[Document]: Documents with structured graph data
        """
        # First load documents using the parent class method
        documents = super().load_data(
            file=file,
            include_sheetname=include_sheetname,
            sheet_name=sheet_name,
            extra_info=extra_info,
            **kwargs
        )
        
        if not extract_relationships:
            return documents
        
        # Extract relationships from the documents
        graph_documents = []
        for doc in documents:
            # Create entity document
            entity_doc = Document(
                text=doc.text,
                metadata={
                    **doc.metadata,
                    "node_type": "entity",
                    "entity_type": "equipment",
                }
            )
            graph_documents.append(entity_doc)
            
            # Extract relationships
            relationships = self._extract_relationships(doc)
            for rel_type, rel_target, rel_props in relationships:
                # Create relationship document
                rel_doc = Document(
                    text=f"{doc.metadata.get('entity_id')} {rel_type} {rel_target}",
                    metadata={
                        "node_type": "relationship",
                        "relationship_type": rel_type,
                        "source_id": doc.metadata.get("entity_id"),
                        "target_id": rel_target,
                        "properties": rel_props,
                        "source_file": doc.metadata.get("source_file"),
                    }
                )
                graph_documents.append(rel_doc)
        
        return graph_documents
    
    def _extract_relationships(self, doc: Document) -> List[Tuple[str, str, Dict[str, Any]]]:
        """Extract relationships from a document.
        
        Args:
            doc (Document): The document to extract relationships from
            
        Returns:
            List[Tuple[str, str, Dict]]: List of (relationship_type, target_id, properties)
        """
        relationships = []
        metadata = doc.metadata
        entity_id = metadata.get("entity_id", "")
        
        # Extract signal type relationship
        signal_type = metadata.get("signal_type", "")
        if signal_type:
            rel_type = self._relationship_mapping.get("signal_type", "HAS_SIGNAL_TYPE")
            relationships.append((rel_type, signal_type, {"confidence": 1.0}))
        
        # Extract processing method relationship
        processing_method = metadata.get("processing_method", "")
        if processing_method:
            rel_type = self._relationship_mapping.get("processing_method", "HAS_PROCESSING_METHOD")
            relationships.append((rel_type, processing_method, {"confidence": 1.0}))
        
        # Extract category relationships
        categories = metadata.get("categories", {})
        for cat_key, cat_value in categories.items():
            if cat_value and cat_key not in ["signal_type", "processing_method"]:
                rel_type = self._relationship_mapping.get(cat_key, f"HAS_{cat_key.upper()}")
                relationships.append((rel_type, cat_value, {"category": cat_key}))
        
        return relationships