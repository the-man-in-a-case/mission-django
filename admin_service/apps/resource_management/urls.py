from django.urls import path
from .views import (
    ResourceImportJobViewSet,
    MapExportAPIView, LayerExportAPIView,
    MapListAPIView, LayerListAPIView
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'import-jobs', ResourceImportJobViewSet)

urlpatterns = [
    path('export/map/<int:id>/', MapExportAPIView.as_view(), name='export-map'),
    path('export/layer/<int:id>/', LayerExportAPIView.as_view(), name='export-layer'),
    path('export/map/latest/', LatestMapExportAPIView.as_view(), name='export-latest-map'),  # 新增
    path('export/layer/latest/', LatestLayerExportAPIView.as_view(), name='export-latest-layer'),  # 新增
    path('maps/', MapListAPIView.as_view(), name='list-maps'),
    path('layers/', LayerListAPIView.as_view(), name='list-layers'),
] + router.urls

"""
POST /resource-management/import-jobs/
{
    "import_type": "layer",
    "api_data": {
        "type": "PowerLayer",
        "version_number": "v1.2",
        "author": "admin",
        "message": "电网图层导入",
        "nodes": [
            {
                "base_node_name": "变电站A",
                "cis_type": "002",
                "sub_type": "2-1Gen",
                "nation": "中国",
                "province": "江苏省",
                "city": "南京市"
            }
        ]
    }
}
output:
{
    "id": 1,
    "import_type": "layer",
    "target_id": 5,  // 新创建的Layer ID
    "status": "success",
    "log": "成功通过API创建Layer（ID=5）\n成功导入1个节点\nLayer级联导入完成",
    "created_at": "2024-05-20T14:30:00Z",
    "updated_at": "2024-05-20T14:31:00Z"
}
---
GET /resource-management/maps/1/export/
output:
{
    "id": 1,
    "version_number": "v2.0",
    "layers": [
        {
            "id": 5,
            "type": "PowerLayer",
            "version_number": "v1.2",
            "nodes": [
                {
                    "base_node_name": "变电站A",
                    "cis_type": "002",
                    "sub_type": "2-1Gen"
                }
            ]
        }
    ]
}
"""