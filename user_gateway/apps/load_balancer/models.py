from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from ..userdb.models import User, UserContainer, ContainerInstance  # 引用userdb中的ContainerInstance

class RouteRegistry(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='route_registry')
    container = models.OneToOneField(UserContainer, on_delete=models.CASCADE, related_name='route_registry')
    
    route_path = models.CharField(max_length=200, verbose_name='路由路径')
    target_service = models.CharField(max_length=100, verbose_name='目标服务名')
    target_namespace = models.CharField(max_length=50, default='user-containers', verbose_name='目标命名空间')
    
    load_balance_strategy = models.CharField(
        max_length=20, 
        choices=[
            ('round_robin', '轮询'),
            ('least_conn', '最少连接'),
            ('weighted', '权重'),
            ('ip_hash', 'IP哈希'),
            ('response_time', '响应时间'),
        ],
        default='round_robin',
        verbose_name='负载均衡策略'
    )
    
    health_check_enabled = models.BooleanField(default=True, verbose_name='启用健康检查')
    health_check_path = models.CharField(max_length=200, default='/health', verbose_name='健康检查路径')
    health_check_interval = models.IntegerField(default=30, verbose_name='健康检查间隔(秒)')
    health_check_timeout = models.IntegerField(default=5, verbose_name='健康检查超时(秒)')
    max_failures = models.IntegerField(default=3, verbose_name='最大失败次数')
    
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    last_route_time = models.DateTimeField(null=True, blank=True, verbose_name='最后路由时间')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'route_registry'
        verbose_name = '路由注册表'
        verbose_name_plural = '路由注册表'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['is_active', 'created_at']),
        ]
    
    def __str__(self):
        return f"Route for User {self.user.username}"
    
    def update_route_time(self):
        self.last_route_time = timezone.now()
        self.save(update_fields=['last_route_time'])

class LoadBalancerConfig(models.Model):
    route_registry = models.OneToOneField(RouteRegistry, on_delete=models.CASCADE, related_name='load_balancer_config', verbose_name='路由注册')
    
    max_connections = models.IntegerField(default=100, verbose_name='最大连接数')
    connection_timeout = models.IntegerField(default=30, verbose_name='连接超时(秒)')
    idle_timeout = models.IntegerField(default=60, verbose_name='空闲超时(秒)')
    
    retry_attempts = models.IntegerField(default=3, verbose_name='重试次数')
    retry_delay = models.FloatField(default=1.0, verbose_name='重试延迟(秒)')
    
    circuit_breaker_enabled = models.BooleanField(default=True, verbose_name='启用熔断器')
    failure_threshold = models.IntegerField(default=5, verbose_name='失败阈值')
    recovery_timeout = models.IntegerField(default=60, verbose_name='恢复超时(秒)')
    
    rate_limit_enabled = models.BooleanField(default=False, verbose_name='启用限流')
    requests_per_minute = models.IntegerField(default=1000, verbose_name='每分钟请求数')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'load_balancer_config'
        verbose_name = '负载均衡配置'
        verbose_name_plural = '负载均衡配置'
    
    def __str__(self):
        return f"LB Config for Route {self.route_registry.user.username}"

class RouteMetrics(models.Model):
    route_registry = models.OneToOneField(RouteRegistry, on_delete=models.CASCADE, related_name='metrics', verbose_name='路由注册')
    
    total_requests = models.BigIntegerField(default=0, verbose_name='总请求数')
    successful_requests = models.BigIntegerField(default=0, verbose_name='成功请求数')
    failed_requests = models.BigIntegerField(default=0, verbose_name='失败请求数')
    
    avg_response_time = models.FloatField(default=0.0, verbose_name='平均响应时间(ms)')
    min_response_time = models.FloatField(default=0.0, verbose_name='最小响应时间(ms)')
    max_response_time = models.FloatField(default=0.0, verbose_name='最大响应时间(ms)')
    
    timeout_count = models.IntegerField(default=0, verbose_name='超时次数')
    connection_error_count = models.IntegerField(default=0, verbose_name='连接错误次数')
    server_error_count = models.IntegerField(default=0, verbose_name='服务器错误次数')
    
    last_request_time = models.DateTimeField(null=True, blank=True, verbose_name='最后请求时间')
    reset_time = models.DateTimeField(auto_now_add=True, verbose_name='重置时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'route_metrics'
        verbose_name = '路由指标'
        verbose_name_plural = '路由指标'
    
    def __str__(self):
        return f"Metrics for {self.route_registry.user.username}"
    
    @property
    def success_rate(self):
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def update_metrics(self, response_time, success=True, error_type=None):
        self.total_requests += 1
        self.last_request_time = timezone.now()
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            if error_type == 'timeout':
                self.timeout_count += 1
            elif error_type == 'connection':
                self.connection_error_count += 1
            elif error_type == 'server':
                self.server_error_count += 1
        
        if self.total_requests == 1:
            self.avg_response_time = response_time
            self.min_response_time = response_time
            self.max_response_time = response_time
        else:
            self.avg_response_time = (
                (self.avg_response_time * (self.total_requests - 1) + response_time) 
                / self.total_requests
            )
            self.min_response_time = min(self.min_response_time, response_time)
            self.max_response_time = max(self.max_response_time, response_time)
        
        self.save()
    
    def reset_metrics(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.avg_response_time = 0.0
        self.min_response_time = 0.0
        self.max_response_time = 0.0
        self.timeout_count = 0
        self.connection_error_count = 0
        self.server_error_count = 0
        self.reset_time = timezone.now()
        self.save()

class RouteLog(models.Model):
    route_registry = models.ForeignKey(RouteRegistry, on_delete=models.CASCADE, related_name='logs', verbose_name='路由注册')
    container_instance = models.ForeignKey(ContainerInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name='route_logs', verbose_name='容器实例')  # 引用userdb的ContainerInstance
    
    request_id = models.CharField(max_length=100, db_index=True, verbose_name='请求ID')
    request_method = models.CharField(max_length=10, verbose_name='请求方法')
    request_path = models.CharField(max_length=500, verbose_name='请求路径')
    request_headers = models.JSONField(default=dict, blank=True, verbose_name='请求头')
    client_ip = models.GenericIPAddressField(verbose_name='客户端IP')
    user_agent = models.TextField(blank=True, verbose_name='用户代理')
    
    target_url = models.CharField(max_length=500, verbose_name='目标URL')
    load_balance_strategy = models.CharField(max_length=20, verbose_name='负载均衡策略')
    
    response_status = models.IntegerField(null=True, blank=True, verbose_name='响应状态码')
    response_time = models.FloatField(null=True, blank=True, verbose_name='响应时间(ms)')
    response_size = models.BigIntegerField(null=True, blank=True, verbose_name='响应大小(bytes)')
    
    error_type = models.CharField(
        max_length=20, 
        choices=[
            ('timeout', '超时'),
            ('connection', '连接错误'),
            ('server', '服务器错误'),
            ('client', '客户端错误'),
            ('gateway', '网关错误'),
        ],
        null=True, blank=True, verbose_name='错误类型'
    )
    error_message = models.TextField(null=True, blank=True, verbose_name='错误信息')
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='时间戳')
    
    class Meta:
        db_table = 'route_logs'
        verbose_name = '路由日志'
        verbose_name_plural = '路由日志'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['route_registry', 'timestamp']),
            models.Index(fields=['request_id']),
            models.Index(fields=['response_status', 'timestamp']),
            models.Index(fields=['error_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"Route Log - {self.route_registry.user.username} at {self.timestamp}"

class HealthCheckRecord(models.Model):
    container_instance = models.ForeignKey(ContainerInstance, on_delete=models.CASCADE, related_name='health_records', verbose_name='容器实例')  # 引用userdb的ContainerInstance
    
    is_healthy = models.BooleanField(verbose_name='是否健康')
    response_time = models.FloatField(null=True, blank=True, verbose_name='响应时间(ms)')
    status_code = models.IntegerField(null=True, blank=True, verbose_name='状态码')
    
    check_url = models.CharField(max_length=200, verbose_name='检查URL')
    error_message = models.TextField(null=True, blank=True, verbose_name='错误信息')
    details = models.JSONField(default=dict, blank=True, verbose_name='详细信息')
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='检查时间')
    
    class Meta:
        db_table = 'health_check_records'
        verbose_name = '健康检查记录'
        verbose_name_plural = '健康检查记录'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['container_instance', 'timestamp']),
            models.Index(fields=['is_healthy', 'timestamp']),
        ]
    
    def __str__(self):
        status = "健康" if self.is_healthy else "不健康"
        return f"{self.container_instance} - {status} at {self.timestamp}"
