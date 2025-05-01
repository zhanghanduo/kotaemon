"""Index configuration for the application."""
from kotaemon.indices.maintenance_index import MaintenanceIndex

def register_maintenance_index(index_manager):
    """Register the maintenance index with the index manager."""
    maintenance_index = MaintenanceIndex(
        name="设备维护数据",
        id="maintenance",
        description="设备维护记录和故障分析索引"
    )
    index_manager.register(maintenance_index)