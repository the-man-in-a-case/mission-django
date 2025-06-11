from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContainerRegistryViewSet, RouteMetricsViewSet

app_name = 'route_management'

router = DefaultRouter()
router.register(r'containers', ContainerRegistryViewSet)
router.register(r'metrics', RouteMetricsViewSet)

urlpatterns = [
    path('api/route/', include(router.urls)),
]
