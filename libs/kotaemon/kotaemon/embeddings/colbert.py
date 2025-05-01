# 添加模型配置以解决命名冲突警告
from pydantic import ConfigDict

class ColPaliEmbeddings(BaseEmbeddings):
    # 添加模型配置
    model_config = ConfigDict(protected_namespaces=())
    
    # 其他代码保持不变...