from django.urls import path
from .views import IndustryNodeOptimizeAPI, OptimizedPathHighlightView

urlpatterns = [
    path("industry-optimize/", IndustryNodeOptimizeAPI.as_view(), name="industry-optimize"),  # 行业节点优化接口
    path('optimized-paths-highlight/', OptimizedPathHighlightView.as_view(), name='optimized-paths-highlight'),  # 优化路径高亮接口
]

"""
GET api/optimized-paths-highlight/?task_id=your_task_id
{
    "message": "成功获取高亮路径数据",
    "data": {
        "001": [
            {
                "directed": false,
                "graph": {},
                "nodes": [
                    {"id": "node1", "is_optimized": true, "voltage": "220kV"},
                    {"id": "node2", "is_optimized": true, "capacity": "500MVA"}
                ],
                "links": [
                    {"source": "node1", "target": "node2", "is_optimized": true, "resistance": "0.5Ω"}
                ],
                "multigraph": false
            },
            // 其他路径的高亮子图...
        ],
        "002": null  // 无有效路径或原Graph缺失
    }
}
    高亮标记：通过为节点/边添加 is_optimized: true 属性，前端可直接根据该字段渲染高亮效果。
"""