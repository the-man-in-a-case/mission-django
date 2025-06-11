from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('business-flow/', include('apps.business_flow.urls')),  # Fixed import path
    # path('gateway/', include('apps.gateway_client.urls')),  # Fixed import path
]
