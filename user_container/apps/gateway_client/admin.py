from django.contrib import admin
from .models import ServiceInstance, HealthCheckResult, ExceptionReport, ExceptionData, MetricsData

@admin.register(ServiceInstance)
class ServiceInstanceAdmin(admin.ModelAdmin):
    list_display = ['service_id', 'service_type', 'host', 'port', 'health_status', 'last_health_check', 'registered_at']
    list_filter = ['health_status', 'service_type', 'registered_at']
    search_fields = ['service_id', 'host']
    readonly_fields = ['registered_at']

@admin.register(ExceptionData)
class ExceptionDataAdmin(admin.ModelAdmin):
    list_display = ['container_id', 'service_name', 'source', 'exception_type', 'severity', 'is_reported', 'timestamp']
    list_filter = ['source', 'severity', 'is_reported', 'service_name', 'timestamp']
    search_fields = ['container_id', 'service_name', 'exception_message']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

@admin.register(MetricsData)
class MetricsDataAdmin(admin.ModelAdmin):
    list_display = ['service_id', 'metric_name', 'metric_value', 'timestamp']
    list_filter = ['metric_name', 'timestamp']
    search_fields = ['service_id', 'metric_name']
    readonly_fields = ['timestamp']
