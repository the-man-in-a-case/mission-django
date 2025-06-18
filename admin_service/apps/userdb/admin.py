from django.contrib import admin
from .models import (
    User, UserActivity, UserContainer, ContainerInstance, 
    RouteRegistry, LoadBalancerConfig, RouteMetrics, 
    RouteLog, HealthCheckRecord, GatewayNode
)
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'phone', 'permission_level', 'status', 'is_staff', 'created_at')
    list_filter = ('permission_level', 'status', 'is_staff', 'created_at')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('个人信息', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('权限', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('用户状态', {'fields': ('permission_level', 'status')}),
        ('容器信息', {'fields': ('container_id', 'container_status')}),
        ('资源限制', {'fields': ('cpu_limit', 'memory_limit', 'storage_limit')}),
        ('时间信息', {'fields': ('last_login_at', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'permission_level', 'status'),
        }),
    )
    search_fields = ('username', 'email', 'phone')
    ordering = ('-created_at',)

class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'created_at', 'ip_address')
    list_filter = ('action', 'created_at')
    search_fields = ('user__username', 'ip_address')
    raw_id_fields = ('user',)
    ordering = ('-created_at',)

class UserContainerAdmin(admin.ModelAdmin):
    list_display = ('user', 'container_name', 'status', 'replicas', 'ready_replicas', 'created_at')
    list_filter = ('status', 'namespace', 'created_at')
    search_fields = ('user__username', 'container_name', 'deployment_name', 'service_name')
    raw_id_fields = ('user',)
    ordering = ('-created_at',)
    readonly_fields = ('service_url', 'is_ready')
    fieldsets = (
        (None, {'fields': ('user', 'container_name', 'status')}),
        ('Kubernetes配置', {'fields': ('deployment_name', 'service_name', 'namespace', 'cluster_ip', 'external_ip', 'port')}),
        ('副本信息', {'fields': ('replicas', 'ready_replicas')}),
        ('资源配置', {'fields': ('cpu_request', 'memory_request', 'cpu_limit', 'memory_limit', 'storage_size')}),
        ('时间信息', {'fields': ('created_at', 'updated_at', 'last_accessed')}),
        ('元数据', {'fields': ('labels', 'annotations', 'environment_vars')}),
        ('状态信息', {'fields': ('service_url', 'is_ready')}),
    )

class ContainerInstanceAdmin(admin.ModelAdmin):
    list_display = ('container', 'instance_id', 'pod_name', 'status', 'is_healthy', 'weight', 'current_connections', 'last_health_check')
    list_filter = ('status', 'is_healthy', 'container__user__username')
    search_fields = ('instance_id', 'pod_name', 'container__user__username')
    raw_id_fields = ('container',)
    ordering = ('-created_at',)
    readonly_fields = ('service_url', 'is_available')
    fieldsets = (
        (None, {'fields': ('container', 'instance_id', 'pod_name', 'status')}),
        ('网络配置', {'fields': ('pod_ip', 'port')}),
        ('健康状态', {'fields': ('is_healthy', 'consecutive_failures', 'last_health_check', 'health_check_url')}),
        ('负载均衡', {'fields': ('weight', 'current_connections')}),
        ('时间信息', {'fields': ('created_at', 'updated_at')}),
        ('状态信息', {'fields': ('service_url', 'is_available')}),
    )

class RouteRegistryAdmin(admin.ModelAdmin):
    list_display = ('user', 'route_path', 'target_service', 'target_namespace', 'load_balance_strategy', 'is_active', 'created_at')
    list_filter = ('load_balance_strategy', 'is_active', 'health_check_enabled', 'created_at')
    search_fields = ('user__username', 'route_path', 'target_service')
    raw_id_fields = ('user', 'container')
    ordering = ('-created_at',)
    fieldsets = (
        (None, {'fields': ('user', 'container', 'route_path', 'is_active')}),
        ('目标服务', {'fields': ('target_service', 'target_namespace')}),
        ('负载均衡', {'fields': ('load_balance_strategy',)}),
        ('健康检查', {'fields': ('health_check_enabled', 'health_check_path', 'health_check_interval', 'health_check_timeout', 'max_failures')}),
        ('时间信息', {'fields': ('created_at', 'updated_at', 'last_route_time')}),
    )

class LoadBalancerConfigAdmin(admin.ModelAdmin):
    list_display = ('route_registry', 'max_connections', 'connection_timeout', 'circuit_breaker_enabled', 'rate_limit_enabled')
    list_filter = ('circuit_breaker_enabled', 'rate_limit_enabled')
    search_fields = ('route_registry__user__username',)
    raw_id_fields = ('route_registry',)
    fieldsets = (
        (None, {'fields': ('route_registry',)}),
        ('连接配置', {'fields': ('max_connections', 'connection_timeout', 'idle_timeout')}),
        ('重试配置', {'fields': ('retry_attempts', 'retry_delay')}),
        ('熔断器配置', {'fields': ('circuit_breaker_enabled', 'failure_threshold', 'recovery_timeout')}),
        ('限流配置', {'fields': ('rate_limit_enabled', 'requests_per_minute')}),
        ('时间信息', {'fields': ('created_at', 'updated_at')}),
    )

class RouteMetricsAdmin(admin.ModelAdmin):
    list_display = ('route_registry', 'total_requests', 'successful_requests', 'failed_requests', 'success_rate', 'avg_response_time', 'last_request_time')
    list_filter = ('route_registry__user__username',)
    search_fields = ('route_registry__user__username',)
    raw_id_fields = ('route_registry',)
    readonly_fields = ('success_rate', 'total_requests', 'successful_requests', 'failed_requests', 
                       'avg_response_time', 'min_response_time', 'max_response_time', 
                       'timeout_count', 'connection_error_count', 'server_error_count',
                       'last_request_time', 'reset_time')
    fieldsets = (
        (None, {'fields': ('route_registry',)}),
        ('请求统计', {'fields': ('total_requests', 'successful_requests', 'failed_requests', 'success_rate')}),
        ('响应时间', {'fields': ('avg_response_time', 'min_response_time', 'max_response_time')}),
        ('错误统计', {'fields': ('timeout_count', 'connection_error_count', 'server_error_count')}),
        ('时间信息', {'fields': ('last_request_time', 'reset_time', 'updated_at')}),
    )
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False

class RouteLogAdmin(admin.ModelAdmin):
    list_display = ('route_registry', 'request_id', 'request_method', 'request_path', 'response_status', 'response_time', 'timestamp')
    list_filter = ('request_method', 'response_status', 'error_type', 'timestamp', 'route_registry__user__username')
    search_fields = ('request_id', 'request_path', 'client_ip', 'route_registry__user__username')
    raw_id_fields = ('route_registry', 'container_instance')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp', 'request_id', 'request_method', 'request_path', 'request_headers', 
                       'client_ip', 'user_agent', 'target_url', 'load_balance_strategy',
                       'response_status', 'response_time', 'response_size', 'error_type', 'error_message')
    fieldsets = (
        (None, {'fields': ('route_registry', 'container_instance', 'timestamp')}),
        ('请求信息', {'fields': ('request_id', 'request_method', 'request_path', 'request_headers', 'client_ip', 'user_agent')}),
        ('路由信息', {'fields': ('target_url', 'load_balance_strategy')}),
        ('响应信息', {'fields': ('response_status', 'response_time', 'response_size')}),
        ('错误信息', {'fields': ('error_type', 'error_message')}),
    )
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

class HealthCheckRecordAdmin(admin.ModelAdmin):
    list_display = ('container_instance', 'is_healthy', 'status_code', 'response_time', 'timestamp')
    list_filter = ('is_healthy', 'status_code', 'timestamp', 'container_instance__container__user__username')
    search_fields = ('container_instance__instance_id', 'container_instance__pod_name', 'error_message')
    raw_id_fields = ('container_instance',)
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp', 'is_healthy', 'status_code', 'response_time', 'check_url', 'error_message', 'details')
    fieldsets = (
        (None, {'fields': ('container_instance', 'timestamp')}),
        ('检查结果', {'fields': ('is_healthy', 'status_code', 'response_time')}),
        ('请求信息', {'fields': ('check_url',)}),
        ('错误信息', {'fields': ('error_message', 'details')}),
    )
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False

class GatewayNodeAdmin(admin.ModelAdmin):
    list_display = ('node_id', 'hostname', 'ip_address', 'is_active', 'cpu_usage', 'memory_usage', 'current_connections', 'total_requests', 'last_heartbeat')
    list_filter = ('is_active', 'last_heartbeat')
    search_fields = ('node_id', 'hostname', 'ip_address')
    readonly_fields = ('is_healthy', 'last_heartbeat', 'created_at')
    fieldsets = (
        (None, {'fields': ('node_id', 'hostname', 'ip_address', 'port', 'is_active')}),
        ('资源使用', {'fields': ('cpu_usage', 'memory_usage')}),
        ('连接统计', {'fields': ('current_connections', 'total_requests')}),
        ('状态信息', {'fields': ('last_heartbeat', 'is_healthy', 'created_at')}),
    )

from .models import AlertRule  

@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    """监控警报规则管理后台"""
    list_display = ('container_instance', 'level', 'is_active', 'created_at', 'triggered_at')
    list_filter = ('level', 'is_active')
    search_fields = ('message', 'trigger_condition')
    raw_id_fields = ('container_instance',)  
    date_hierarchy = 'created_at'  
    readonly_fields = ('created_at',)
    fieldsets = (
        ('基础信息', {
            'fields': ('container_instance', 'level', 'is_active')
        }),
        ('规则详情', {
            'fields': ('trigger_condition', 'message')
        }),
        ('时间信息', {
            'fields': ('created_at', 'triggered_at'),
            'classes': ('collapse',)
        }),
    )

admin.site.register(User, UserAdmin)
admin.site.register(UserActivity, UserActivityAdmin)
admin.site.register(UserContainer, UserContainerAdmin)
admin.site.register(ContainerInstance, ContainerInstanceAdmin)
admin.site.register(RouteRegistry, RouteRegistryAdmin)
admin.site.register(LoadBalancerConfig, LoadBalancerConfigAdmin)
admin.site.register(RouteMetrics, RouteMetricsAdmin)
admin.site.register(RouteLog, RouteLogAdmin)
admin.site.register(HealthCheckRecord, HealthCheckRecordAdmin)
admin.site.register(GatewayNode, GatewayNodeAdmin)    