# Machine Maintenance Data Loaders

This directory contains specialized loaders for processing machine maintenance data from Excel files, with a focus on equipment signals, processing methods, and knowledge graph construction.

## Available Loaders

### MaintenanceDataLoader

A basic loader for maintenance data that extends the `ExcelReader`. It provides automatic column detection for:

- Equipment/entity identifiers
- Description fields
- Category information

```python
from kotaemon.loaders import MaintenanceDataLoader

loader = MaintenanceDataLoader()
documents = loader.load_data("path/to/maintenance_data.xlsx")
```

### SignalDataLoader

A specialized loader for machine signal data that extends `MaintenanceDataLoader`. It adds specific handling for:

- Signal type detection
- Processing method extraction
- Structured document creation optimized for the format shown in the example

```python
from kotaemon.loaders import SignalDataLoader

loader = SignalDataLoader()
documents = loader.load_data("path/to/signal_data.xlsx")
```

### MaintenanceGraphLoader

A loader that creates knowledge graph-ready data with explicit entity and relationship extraction. It extends `SignalDataLoader` and adds:

- Entity node creation
- Relationship extraction
- Property mapping

```python
from kotaemon.loaders import MaintenanceGraphLoader

loader = MaintenanceGraphLoader()
graph_documents = loader.load_data(
    "path/to/maintenance_data.xlsx", 
    extract_relationships=True
)

# Separate entity and relationship nodes
entity_nodes = [doc for doc in graph_documents if doc.metadata.get("node_type") == "entity"]
relationship_nodes = [doc for doc in graph_documents if doc.metadata.get("node_type") == "relationship"]
```

## Custom Column Specification

All loaders support explicit column specification:

```python
loader = SignalDataLoader(
    entity_columns=["产品型号"],
    description_columns=["信息描述"],
    category_columns=["信号分类"],
    signal_type_column="信号分类",
    processing_method_column="处理方案"
)
```

## Automatic Column Detection

If columns aren't explicitly specified, the loaders will attempt to automatically detect them based on common naming patterns in both English and Chinese:

- Entity columns: "id", "编号", "号", "设备", "产品", "型号", "code", "number", "序号", "产品型号"
- Description columns: "描述", "说明", "信息", "内容", "desc", "description", "info", "detail", "信息描述"
- Category columns: "类别", "类型", "分类", "category", "type", "class", "分类", "处理方案"

## Output Format

The loaders produce `Document` objects with:

- **Text content**: Structured representation of the maintenance data
- **Metadata**: Rich metadata including entity IDs, categories, and relationships

For the graph loader, documents are tagged with `node_type` as either "entity" or "relationship" to facilitate knowledge graph construction.