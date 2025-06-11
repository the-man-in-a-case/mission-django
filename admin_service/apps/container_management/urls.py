from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContainerManagementViewSet

router = DefaultRouter()
router.register(r'containers', ContainerManagementViewSet, basename='container-management')

urlpatterns = [
    path('', include(router.urls)),
]