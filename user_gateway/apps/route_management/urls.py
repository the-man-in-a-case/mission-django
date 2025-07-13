from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContainerRegistryViewSet, RouteMetricsViewSet, CustomAuthToken, TokenManagementViewSet

router = DefaultRouter()
router.register(r'containers', ContainerRegistryViewSet)
router.register(r'metrics', RouteMetricsViewSet)
router.register(r'token', TokenManagementViewSet, basename='token-management')

urlpatterns = [
    path('api/route/', include(router.urls)),
    path('auth/', CustomAuthToken.as_view(), name='token-auth'),
    # 添加业务异常查询端点
    path('api/route/errors/', views.BusinessErrorLogViewSet.as_view({'get': 'list'}), name='business-errors'),
]
