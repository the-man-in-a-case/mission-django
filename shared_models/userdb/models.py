from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from rest_framework.authtoken.models import Token as DRFToken
import binascii
import os

class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True, null=True, verbose_name='手机号')
    is_admin = models.BooleanField(default=False, verbose_name='是否管理员')
    is_regular = models.BooleanField(default=True, verbose_name='是否普通用户')
    tenant_id = models.CharField(max_length=50, unique=True, verbose_name='租户ID')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        indexes = [
            models.Index(fields=['tenant_id']),
            models.Index(fields=['username']),
        ]

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities', verbose_name='用户')
    activity_type = models.CharField(max_length=50, verbose_name='活动类型')
    description = models.TextField(verbose_name='活动描述')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.TextField(blank=True, verbose_name='用户代理')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='时间戳')

    class Meta:
        db_table = 'user_activities'
        verbose_name = '用户活动'
        verbose_name_plural = '用户活动'
        ordering = ['-timestamp']

class UserContainer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='containers', verbose_name='用户')
    container_id = models.CharField(max_length=100, unique=True, verbose_name='容器ID')
    name = models.CharField(max_length=100, verbose_name='容器名称')
    image = models.CharField(max_length=200, verbose_name='镜像名称')
    status = models.CharField(
        max_length=20,
        choices=[('pending', '待处理'), ('running', '运行中'), ('stopped', '已停止'), ('error', '错误')],
        default='pending',
        verbose_name='状态'
    )
    cpu_limit = models.FloatField(default=1.0, verbose_name='CPU限制(核)')
    memory_limit = models.IntegerField(default=512, verbose_name='内存限制(MB)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'user_containers'
        verbose_name = '用户容器'
        verbose_name_plural = '用户容器'

class ContainerInstance(models.Model):
    container = models.ForeignKey(UserContainer, on_delete=models.CASCADE, related_name='instances', verbose_name='容器')
    instance_id = models.CharField(max_length=100, verbose_name='实例ID')
    pod_name = models.CharField(max_length=100, verbose_name='Pod名称')
    pod_ip = models.GenericIPAddressField(verbose_name='Pod IP')
    port = models.IntegerField(verbose_name='端口号')
    status = models.CharField(
        max_length=20,
        choices=[('pending', '待处理'), ('running', '运行中'), ('stopped', '已停止'), ('error', '错误')],
        default='pending',
        verbose_name='状态'
    )
    is_healthy = models.BooleanField(default=False, verbose_name='是否健康')
    consecutive_failures = models.IntegerField(default=0, verbose_name='连续失败次数')
    max_connections = models.IntegerField(default=100, verbose_name='最大连接数')
    health_check_url = models.CharField(max_length=200, blank=True, verbose_name='健康检查URL')
    last_health_check = models.DateTimeField(null=True, blank=True, verbose_name='最后健康检查时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'container_instances'
        verbose_name = '容器实例'
        verbose_name_plural = '容器实例'
        unique_together = ['container', 'instance_id']

# 路由相关模型
class RouteRegistry(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='route_registry')
    container = models.OneToOneField(UserContainer, on_delete=models.CASCADE, related_name='route_registry')
    route_path = models.CharField(max_length=200, verbose_name='路由路径')
    target_service = models.CharField(max_length=100, verbose_name='目标服务名')
    target_namespace = models.CharField(max_length=50, default='user-containers', verbose_name='目标命名空间')
    load_balance_strategy = models.CharField(
        max_length=20, 
        choices=[('round_robin', '轮询'), ('least_conn', '最少连接'), ('weighted', '权重'), ('ip_hash', 'IP哈希'), ('response_time', '响应时间')],
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

# 监控相关模型
class AlertRule(models.Model):
    LEVEL_CHOICES = [('info', '信息'), ('warning', '警告'), ('error', '错误'), ('critical', '严重')]
    RULE_TYPES = [('container_cpu', '容器CPU使用率'), ('container_memory', '容器内存使用率'), ('route_latency', '路由延迟'), ('instance_health', '实例健康状态')]
    container_instance = models.ForeignKey(ContainerInstance, on_delete=models.CASCADE, related_name='alerts', verbose_name='关联容器实例')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='info', verbose_name='警报级别')
    trigger_condition = models.TextField(verbose_name='触发条件')
    message = models.TextField(verbose_name='警报消息')
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    triggered_at = models.DateTimeField(null=True, blank=True, verbose_name='触发时间')
    rule_type = models.CharField(max_length=20, choices=RULE_TYPES, verbose_name='规则类型')
    threshold = models.FloatField(verbose_name='阈值')

    class Meta:
        db_table = 'alert_rules'
        verbose_name = '监控警报规则'
        verbose_name_plural = '监控警报规则'

class ContainerMetric(models.Model):
    container = models.ForeignKey(UserContainer, on_delete=models.CASCADE, related_name='metrics')
    timestamp = models.DateTimeField(default=timezone.now)
    cpu_usage = models.FloatField(help_text='CPU使用率(百分比)')
    memory_usage = models.FloatField(help_text='内存使用率(百分比)')
    disk_usage = models.FloatField(help_text='磁盘使用率(百分比)')
    network_in = models.FloatField(help_text='网络入流量(B/s)')
    network_out = models.FloatField(help_text='网络出流量(B/s)')
    request_count = models.IntegerField(default=0, help_text='请求计数')
    error_count = models.IntegerField(default=0, help_text='错误计数')

    class Meta:
        indexes = [models.Index(fields=['container', 'timestamp'])]

class ResourceAlert(models.Model):
    ALERT_LEVEL_CHOICES = (('info', '信息'), ('warning', '警告'), ('critical', '严重'))
    ALERT_TYPE_CHOICES = (('cpu', 'CPU过载'), ('memory', '内存过载'), ('disk', '磁盘过载'), ('network', '网络异常'), ('health', '健康检查失败'))
    container = models.ForeignKey(UserContainer, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPE_CHOICES)
    level = models.CharField(max_length=10, choices=ALERT_LEVEL_CHOICES, default='warning')
    message = models.TextField()
    triggered_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)
    is_resolved = models.BooleanField(default=False)

# 扩展Token模型
class Token(DRFToken):
    expires_at = models.DateTimeField(default=timezone.now() + timezone.timedelta(days=7))
    is_revoked = models.BooleanField(default=False)
    scope = models.CharField(max_length=255, blank=True, help_text="Token权限范围，多个用逗号分隔")
    last_used = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'auth_token'
        verbose_name = 'Token'
        verbose_name_plural = 'Tokens'

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)

    @classmethod
    def generate_key(cls):
        return binascii.hexlify(os.urandom(20)).decode()


class BusinessErrorLog(models.Model):
    container_instance = models.ForeignKey(ContainerInstance, on_delete=models.CASCADE, related_name='error_logs')
    error_type = models.CharField(max_length=50, verbose_name='异常类型')
    error_message = models.TextField(verbose_name='异常消息')
    stack_trace = models.TextField(blank=True, null=True, verbose_name='堆栈跟踪')
    occurred_at = models.DateTimeField(default=timezone.now, verbose_name='发生时间')
    is_resolved = models.BooleanField(default=False, verbose_name='是否已解决')
    resolved_at = models.DateTimeField(blank=True, null=True, verbose_name='解决时间')

    class Meta:
        db_table = 'business_error_logs'
        verbose_name = '业务异常日志'
        verbose_name_plural = '业务异常日志'
        ordering = ['-occurred_at']


class ContainerMetric(models.Model):
    container = models.ForeignKey(UserContainer, on_delete=models.CASCADE, related_name='metrics')
    timestamp = models.DateTimeField(default=timezone.now)
    cpu_usage = models.FloatField(help_text='CPU使用率(百分比)')
    memory_usage = models.FloatField(help_text='内存使用率(百分比)')
    disk_usage = models.FloatField(help_text='磁盘使用率(百分比)')
    network_in = models.FloatField(help_text='网络入流量(B/s)')
    network_out = models.FloatField(help_text='网络出流量(B/s)')
    request_count = models.IntegerField(default=0, help_text='请求计数')
    error_count = models.IntegerField(default=0, help_text='错误计数')
    # 新增业务异常字段
    business_error_count = models.IntegerField(default=0, help_text='业务异常计数')
    last_business_error = models.TextField(blank=True, null=True, help_text='最后一次业务异常详情')

    class Meta:
        indexes = [models.Index(fields=['container', 'timestamp'])]