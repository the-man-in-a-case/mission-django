from django.urls import path
from .views import register_service, report_health

urlpatterns = [
    path('register/', register_service, name='register_service'),  
    path('health/', report_health, name='report_health'),  
]