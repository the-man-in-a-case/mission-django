from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BusinessFlowViewSet, LatestResourcesAPIView, InfluxDataAPIView  # 添加 InfluxDataAPIView 导入
from .views import CreateTemplateAPI, ListTemplatesAPI, RetrieveTemplateNodesAPI, SimulationDataConsumer, SimulationLogAPIView  # 新增 SimulationLogAPIView 导入


router = DefaultRouter()
router.register(r'business-flow', BusinessFlowViewSet, basename='business-flow')

urlpatterns = [
    path('', include(router.urls)),  # 视图集自动生成的路由（如GET/POST等）
    path('latest-resources/', LatestResourcesAPIView.as_view(), name='latest-resources'),  # 独立视图
    path('influx-data/', InfluxDataAPIView.as_view(), name='influx-data'),  # 独立视图（需确认是否存在）
    path('templates/create/', CreateTemplateAPI.as_view(), name='create-template'),
    path('templates/', ListTemplatesAPI.as_view(), name='list-templates'),
    path('templates/<int:pk>/nodes/', RetrieveTemplateNodesAPI.as_view(), name='retrieve-template-nodes'),
    path('', include(router.urls)),
    path('latest-resources/', LatestResourcesAPIView.as_view(), name='latest-resources'),
    path('influx-data/', InfluxDataAPIView.as_view(), name='influx-data'),
    path('templates/create/', CreateTemplateAPI.as_view(), name='create-template'),
    path('templates/', ListTemplatesAPI.as_view(), name='list-templates'),
    path('templates/<int:pk>/nodes/', RetrieveTemplateNodesAPI.as_view(), name='retrieve-template-nodes'),
    path('simulation-data/', SimulationDataConsumer.as_asgi(), name='simulation-data'),  # 新增WebSocket路由
    path('simulation-log/', SimulationLogAPIView.as_view(), name='simulation-log'),  # 新增SSE路由
    path('business-flow/<int:pk>/task-template/<int:template_id>/', BusinessFlowViewSet.as_view({'get': 'retrieve_task_template'}), name='retrieve-task-template'),   #新增接口十二路由
]