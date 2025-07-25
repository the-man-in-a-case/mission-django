from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContainerRegistryViewSet, 
    RouteMetricsViewSet, 
    CustomAuthToken, 
    TokenManagementViewSet, 
    BusinessErrorLogViewSet, 
    receive_exception_report
)

router = DefaultRouter()
router.register(r'containers', ContainerRegistryViewSet)
router.register(r'metrics', RouteMetricsViewSet)
router.register(r'token', TokenManagementViewSet, basename='token-management')

urlpatterns = [
    path('api/route/', include(router.urls)),
    path('auth/', CustomAuthToken.as_view(), name='token-auth'),
    path('api/route/errors/', BusinessErrorLogViewSet.as_view({'get': 'list'}), name='business-errors'),
    path('api/exceptions/report/', receive_exception_report, name='receive-exceptions'),
]
