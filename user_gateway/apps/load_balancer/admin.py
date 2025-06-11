from django.contrib import admin
from .models import RouteRegistry, LoadBalancerConfig, RouteMetrics, RouteLog, HealthCheckRecord

@admin.register(RouteRegistry)
class RouteRegistryAdmin(admin.ModelAdmin):
    list_display = ('user', 'route_path', 'load_balance_strategy', 'is_active')
    list_filter = ('is_active', 'load_balance_strategy')
    search_fields = ('user__username', 'route_path')

@admin.register(LoadBalancerConfig)
class LoadBalancerConfigAdmin(admin.ModelAdmin):
    list_display = ('route_registry', 'max_connections', 'circuit_breaker_enabled')
    raw_id_fields = ('route_registry',)

@admin.register(RouteMetrics)
class RouteMetricsAdmin(admin.ModelAdmin):
    list_display = ('route_registry', 'total_requests', 'success_rate')
    readonly_fields = ('success_rate',)

@admin.register(RouteLog)
class RouteLogAdmin(admin.ModelAdmin):
    list_display = ('route_registry', 'request_id', 'response_status', 'timestamp')
    list_filter = ('response_status', 'error_type')
    search_fields = ('request_id', 'client_ip')

@admin.register(HealthCheckRecord)
class HealthCheckRecordAdmin(admin.ModelAdmin):
    list_display = ('container_instance', 'is_healthy', 'timestamp')
    list_filter = ('is_healthy',)
    raw_id_fields = ('container_instance',)
