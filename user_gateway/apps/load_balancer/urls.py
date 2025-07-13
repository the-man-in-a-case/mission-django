from django.urls import path
from .views import get_healthy_instances

urlpatterns = [
    path('instances/<str:tenant_id>/healthy/', get_healthy_instances, name='get-healthy-instances'),
]