from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContainerMonitoringViewSet, InstanceHealthViewSet,
    RoutePerformanceView, AlertRuleViewSet
)

router = DefaultRouter()
router.register(r'containers', ContainerMonitoringViewSet, basename='container-metrics')
router.register(r'instances', InstanceHealthViewSet, basename='instance-health')
router.register(r'routes', RoutePerformanceView, basename='route-performance')
router.register(r'alerts/rules', AlertRuleViewSet, basename='alert-rules')

urlpatterns = [
    path('', include(router.urls)),
]