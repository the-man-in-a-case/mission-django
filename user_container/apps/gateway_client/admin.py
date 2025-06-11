from django.contrib import admin
from .models import ServiceInstance

@admin.register(ServiceInstance)
class ServiceInstanceAdmin(admin.ModelAdmin):
    list_display = ('service_id', 'host', 'port', 'last_heartbeat', 'is_healthy')
    search_fields = ('service_id', 'host')
    list_filter = ('is_healthy',)
    readonly_fields = ('last_heartbeat',)
