from django.contrib import admin
from .models import ServiceInstance, HealthCheckResult, ExceptionReport

@admin.register(ServiceInstance)
class ServiceInstanceAdmin(admin.ModelAdmin):
    list_display = ['service_id', 'service_type', 'host', 'port', 'is_healthy', 'last_heartbeat', 'registered_at']
    list_filter = ['is_healthy', 'service_type', 'registered_at']
    search_fields = ['service_id', 'host']
    readonly_fields = ['registered_at']

@admin.register(HealthCheckResult)
class HealthCheckResultAdmin(admin.ModelAdmin):
    list_display = ['service_instance', 'status', 'response_time', 'checked_at']
    list_filter = ['status', 'checked_at']
    search_fields = ['service_instance__service_id']
    readonly_fields = ['checked_at']

@admin.register(ExceptionReport)
class ExceptionReportAdmin(admin.ModelAdmin):
    list_display = ['service_instance', 'exception_type', 'reported_at', 'reported_to']
    list_filter = ['exception_type', 'reported_at']
    search_fields = ['service_instance__service_id', 'exception_message']
    readonly_fields = ['reported_at']
