from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContainerRegistryViewSet, RouteMetricsViewSet, CustomAuthToken

app_name = 'route_management'

router = DefaultRouter()
router.register(r'containers', ContainerRegistryViewSet)
router.register(r'metrics', RouteMetricsViewSet)

urlpatterns = [
    path('api/route/', include(router.urls)),
    path('api/token/', CustomAuthToken.as_view(), name='api_token_auth'),  # 添加Token获取端点
]
