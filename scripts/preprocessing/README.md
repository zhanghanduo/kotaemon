# 维护数据预处理工具

本目录包含用于清洗和加载设备维护数据的脚本，为后续RAG（检索增强生成）应用做准备。

## 文件说明

- `data/collection_raw.xlsx`: 原始维护数据Excel文件
- `data/collection_cleaned.xlsx`: 清洗后的数据（由`clean_maintenance_data.py`生成）
- `data/collection_cleaned.csv`: 清洗后的数据CSV格式（便于查看）
- `clean_maintenance_data.py`: 数据清洗和标准化脚本
- `load_maintenance_data.py`: 数据加载脚本，用于后续RAG应用

## 数据清洗脚本 (clean_maintenance_data.py)

该脚本执行以下操作：

1. **产品型号标准化**：将各种变体统一为'DCS-50FB3+'或'DCS-50LD'
2. **文本清洗**：对信息描述和现场处理方案进行清洗，包括全角转半角、统一换行符、移除多余空格等
3. **问题分类解析**：解析问题分类的层级结构（如"电气系统故障/低压电器故障"）
4. **元数据创建**：为RAG应用创建结构化元数据

### 使用方法

```bash
python clean_maintenance_data.py
```

脚本会自动读取`data/collection_raw.xlsx`，并生成`data/collection_cleaned.xlsx`和`data/collection_cleaned.csv`。

## 数据加载脚本 (load_maintenance_data.py)

该脚本提供了`MaintenanceDataRAGLoader`类，用于加载清洗后的数据并转换为适合RAG应用的格式。

### 主要功能

- 加载清洗后的数据
- 将数据转换为文档列表（包含文本和元数据）
- 按产品型号筛选文档
- 按问题分类筛选文档

### 使用方法

```python
from load_maintenance_data import MaintenanceDataRAGLoader

# 初始化加载器
loader = MaintenanceDataRAGLoader()

# 加载所有数据
df = loader.load_data()

# 获取所有文档
documents = loader.get_documents()

# 按产品型号筛选
fb3_docs = loader.filter_by_product_model("DCS-50FB3+")

# 按问题分类筛选
electrical_docs = loader.filter_by_category("电气系统故障")
```

## 数据统计

清洗后的数据包含以下统计信息：

- 总记录数：500条
- 产品型号分布：
  - DCS-50FB3+：358条
  - DCS-50LD：142条
- 主要问题分类：
  - 电气系统故障：159条
  - 外购设备故障：108条
  - 用户使用操作相关：73条
  - 机械故障：47条
  - 软件系统故障：28条

## 后续RAG应用集成

清洗后的数据可以轻松集成到RAG应用中：

1. 使用`MaintenanceDataRAGLoader`加载文档
2. 将文档导入向量数据库（如Chroma、FAISS等）
3. 利用文档元数据进行精确筛选和检索

这种结构化的数据格式使得RAG应用可以更精确地检索相关维护记录，提高问答和推荐的准确性。