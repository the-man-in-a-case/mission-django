from django.contrib import admin
from .models import ContainerHealthRecord, ExceptionData, ServiceRegistry, MetricsData

@admin.register(ContainerHealthRecord)
class ContainerHealthRecordAdmin(admin.ModelAdmin):
    list_display = ['container_id', 'service_name', 'status', 'timestamp', 'cpu_usage', 'memory_usage']
    list_filter = ['status', 'service_name', 'timestamp']
    search_fields = ['container_id', 'service_name']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

@admin.register(ExceptionData)
class ExceptionDataAdmin(admin.ModelAdmin):
    list_display = ['container_id', 'service_name', 'source', 'exception_type', 'severity', 'is_reported', 'timestamp']
    list_filter = ['source', 'severity', 'is_reported', 'service_name', 'timestamp']
    search_fields = ['container_id', 'service_name', 'exception_message']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

@admin.register(ServiceRegistry)
class ServiceRegistryAdmin(admin.ModelAdmin):
    list_display = ['service_id', 'service_type', 'host', 'port', 'is_active', 'last_heartbeat']
    list_filter = ['is_active', 'service_type', 'registered_at']
    search_fields = ['service_id', 'host']
    readonly_fields = ['registered_at', 'last_heartbeat']

@admin.register(MetricsData)
class MetricsDataAdmin(admin.ModelAdmin):
    list_display = ['service_id', 'metric_name', 'metric_value', 'timestamp']
    list_filter = ['metric_name', 'timestamp']
    search_fields = ['service_id', 'metric_name']
    readonly_fields = ['timestamp']
