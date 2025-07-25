"""
URL configuration for user_gateway project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apps.route_management.views import CustomAuthToken

urlpatterns = [
    path('admin/', admin.site.urls),
    path('prometheus/', include('django_prometheus.urls')),
    path('api/token/', CustomAuthToken.as_view(), name='api_token_auth'),
    path('api/load-balancer/', include('apps.load_balancer.urls')),  # 添加此行
]
