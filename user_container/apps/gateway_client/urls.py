from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_service, name='register-service'),
    path('health/', views.report_health, name='report-health'),
    # 添加业务异常上报端点
    path('report-error/', views.report_business_error, name='report-business-error'),
]