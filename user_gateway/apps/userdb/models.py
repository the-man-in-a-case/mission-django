from django.db import models
import uuid
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    
    PERMISSION_CHOICES = [
        ('basic', '基础用户'),
        ('premium', '高级用户'),
        ('enterprise', '企业用户'),
        ('admin', '管理员'),
    ]
    permission_level = models.CharField(
        max_length=20, 
        choices=PERMISSION_CHOICES, 
        default='basic'
    )
    
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '非活跃'),
        ('suspended', '暂停'),
        ('deleted', '已删除'),
    ]
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='active'
    )
    
    container_id = models.CharField(max_length=255, blank=True, null=True)
    container_status = models.CharField(max_length=50, default='pending')
    
    cpu_limit = models.CharField(max_length=10, default='1000m')
    memory_limit = models.CharField(max_length=10, default='2Gi')
    storage_limit = models.CharField(max_length=10, default='10Gi')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='用户组',
        blank=True,
        help_text='该用户所属的用户组。用户将获得授予其所属每个用户组的所有权限。',
        related_name='custom_user_set',  # 唯一的 related_name
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='用户权限',
        blank=True,
        help_text='该用户的特定权限。',
        related_name='custom_user_set',  # 唯一的 related_name
        related_query_name='custom_user',
    )
    
    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        
    def __str__(self):
        return f"{self.username} ({self.email})"

class UserActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    
    ACTION_CHOICES = [
        ('login', '登录'),
        ('logout', '登出'),
        ('container_start', '容器启动'),
        ('container_stop', '容器停止'),
        ('business_process', '业务流程'),
        ('data_sync', '数据同步'),
    ]
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_activities'
        verbose_name = '用户活动'
        verbose_name_plural = '用户活动'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.created_at}"

class UserContainer(models.Model):
    STATUS_CHOICES = [
        ('creating', '创建中'),
        ('running', '运行中'),
        ('stopped', '已停止'),
        ('error', '错误'),
        ('destroying', '销毁中'),
        ('pending', '等待中'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='container')
    container_name = models.CharField(max_length=100, verbose_name='容器名称')
    
    deployment_name = models.CharField(max_length=100, verbose_name='Deployment名称')
    service_name = models.CharField(max_length=100, verbose_name='Service名称')
    namespace = models.CharField(max_length=50, default='user-containers', verbose_name='命名空间')
    
    cluster_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='集群IP')
    external_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='外部IP')
    port = models.IntegerField(default=8080, verbose_name='端口')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='creating', verbose_name='状态')
    replicas = models.IntegerField(default=1, verbose_name='副本数')
    ready_replicas = models.IntegerField(default=0, verbose_name='就绪副本数')
    
    cpu_request = models.CharField(max_length=20, default='500m', verbose_name='CPU请求')
    memory_request = models.CharField(max_length=20, default='1Gi', verbose_name='内存请求')
    cpu_limit = models.CharField(max_length=20, default='1000m', verbose_name='CPU限制')
    memory_limit = models.CharField(max_length=20, default='2Gi', verbose_name='内存限制')
    storage_size = models.CharField(max_length=20, default='10Gi', verbose_name='存储大小')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    last_accessed = models.DateTimeField(null=True, blank=True, verbose_name='最后访问时间')
    
    labels = models.JSONField(default=dict, blank=True, verbose_name='标签')
    annotations = models.JSONField(default=dict, blank=True, verbose_name='注解')
    environment_vars = models.JSONField(default=dict, blank=True, verbose_name='环境变量')
    
    class Meta:
        db_table = 'user_containers'
        verbose_name = '用户容器'
        verbose_name_plural = '用户容器'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['namespace', 'deployment_name']),
        ]
    
    def __str__(self):
        return f"User-{self.user.username} Container ({self.status})"
    
    @property
    def service_url(self):
        if self.cluster_ip:
            return f"http://{self.cluster_ip}:{self.port}"
        return None
    
    @property
    def is_ready(self):
        return self.status == 'running' and self.ready_replicas >= 1
    
    def update_access_time(self):
        self.last_accessed = timezone.now()
        self.save(update_fields=['last_accessed'])

class ContainerInstance(models.Model):
    INSTANCE_STATUS_CHOICES = [
        ('starting', '启动中'),
        ('running', '运行中'),
        ('stopping', '停止中'),
        ('stopped', '已停止'),
        ('failed', '失败'),
        ('unknown', '未知'),
    ]
    
    container = models.ForeignKey(UserContainer, on_delete=models.CASCADE, related_name='instances', verbose_name='所属容器')
    instance_id = models.CharField(max_length=100, verbose_name='实例ID')
    pod_name = models.CharField(max_length=100, verbose_name='Pod名称')
    
    pod_ip = models.GenericIPAddressField(verbose_name='Pod IP')
    port = models.IntegerField(default=8080, verbose_name='端口')
    
    status = models.CharField(max_length=20, choices=INSTANCE_STATUS_CHOICES, default='starting', verbose_name='状态')
    is_healthy = models.BooleanField(default=False, verbose_name='健康状态')
    consecutive_failures = models.IntegerField(default=0, verbose_name='连续失败次数')
    
    weight = models.IntegerField(
        default=100, 
        verbose_name='权重',
        validators=[MinValueValidator(0), MaxValueValidator(1000)]
    )
    current_connections = models.IntegerField(default=0, verbose_name='当前连接数')
    
    health_check_url = models.CharField(max_length=200, blank=True, verbose_name='健康检查URL')
    last_health_check = models.DateTimeField(null=True, blank=True, verbose_name='最后健康检查时间')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'container_instances'
        verbose_name = '容器实例'
        verbose_name_plural = '容器实例'
        unique_together = ['container', 'instance_id']
        indexes = [
            models.Index(fields=['container', 'status']),
            models.Index(fields=['is_healthy']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.container.user.username}-{self.instance_id} ({self.status})"
    
    @property
    def service_url(self):
        return f"http://{self.pod_ip}:{self.port}"
    
    @property
    def is_available(self):
        return self.status == 'running' and self.is_healthy
    
    def mark_healthy(self):
        self.is_healthy = True
        self.consecutive_failures = 0
        self.last_health_check = timezone.now()
        self.save(update_fields=['is_healthy', 'consecutive_failures', 'last_health_check'])
    
    def mark_unhealthy(self):
        self.is_healthy = False
        self.consecutive_failures += 1
        self.save(update_fields=['is_healthy', 'consecutive_failures'])

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
    container_instance = models.ForeignKey(ContainerInstance, on_delete=models.SET_NULL, null=True, blank=True, related_name='route_logs', verbose_name='容器实例')
    
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
    container_instance = models.ForeignKey(ContainerInstance, on_delete=models.CASCADE, related_name='health_records', verbose_name='容器实例')
    
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

class GatewayNode(models.Model):
    node_id = models.CharField(max_length=100, unique=True, verbose_name='节点ID')
    hostname = models.CharField(max_length=255, verbose_name='主机名')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    port = models.IntegerField(default=8080, verbose_name='端口')
    
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    cpu_usage = models.FloatField(default=0.0, verbose_name='CPU使用率')
    memory_usage = models.FloatField(default=0.0, verbose_name='内存使用率')
    
    current_connections = models.IntegerField(default=0, verbose_name='当前连接数')
    total_requests = models.BigIntegerField(default=0, verbose_name='总请求数')
    
    last_heartbeat = models.DateTimeField(auto_now=True, verbose_name='最后心跳时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    
    class Meta:
        db_table = 'gateway_nodes'
        verbose_name = '网关节点'
        verbose_name_plural = '网关节点'
        indexes = [
            models.Index(fields=['is_active', 'last_heartbeat']),
        ]
    
    def __str__(self):
        return f"Gateway Node {self.node_id} ({self.hostname})"
    
    @property
    def is_healthy(self):
        return (
            self.is_active and 
            timezone.now() - self.last_heartbeat < timezone.timedelta(minutes=2)
        )
from rest_framework.authtoken.models import Token
from django.utils import timezone

class Token(Token):
    expires_at = models.DateTimeField(default=timezone.now() + timezone.timedelta(days=7))
    is_revoked = models.BooleanField(default=False)
    scope = models.CharField(max_length=100, blank=True, default='default')
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'authtoken_token'
        verbose_name = 'Token'
        verbose_name_plural = 'Tokens'

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)