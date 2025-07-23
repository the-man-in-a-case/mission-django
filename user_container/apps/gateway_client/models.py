from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone

class ServiceInstance(models.Model):
    """用户容器服务实例在网关的注册信息"""
    SERVICE_TYPE_CHOICES = [
        ('business_flow', '业务流程服务'),
        ('data_sync', '数据同步服务'),
    ]
    
    HEALTH_STATUS_CHOICES = [
        ('healthy', '健康'),
        ('unhealthy', '异常'),
        ('terminated', '正常结束'),
    ]
    
    service_id = models.CharField(max_length=64, unique=True, help_text="服务唯一ID")
    service_type = models.CharField(max_length=32, choices=SERVICE_TYPE_CHOICES)
    host = models.GenericIPAddressField(help_text="容器服务IP地址")
    port = models.IntegerField(help_text="容器服务端口")
    last_heartbeat = models.DateTimeField(auto_now=True, help_text="最后心跳时间")
    health_status = models.CharField(max_length=20, choices=HEALTH_STATUS_CHOICES, default='healthy')
    
    # 新增字段
    registered_at = models.DateTimeField(auto_now_add=True)
    last_health_check = models.DateTimeField(null=True, blank=True)
    health_check_url = models.URLField(default='http://localhost:8000/healthz')
    metadata = JSONField(default=dict, blank=True)
    
    def __str__(self):
        return f"{self.service_type}-{self.service_id}"

class HealthCheckResult(models.Model):
    """健康检查结果"""
    service_instance = models.ForeignKey(ServiceInstance, on_delete=models.CASCADE, related_name='health_checks')
    is_healthy = models.BooleanField()
    status_code = models.IntegerField(null=True, blank=True)
    response_time = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    checked_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'gateway_client_health_check_result'
        ordering = ['-checked_at']

class ExceptionReport(models.Model):
    """异常上报记录"""
    LEVEL_CHOICES = [
        ('info', '信息'),
        ('warning', '警告'),
        ('error', '错误'),
        ('critical', '严重'),
    ]
    
    service_instance = models.ForeignKey(ServiceInstance, on_delete=models.CASCADE, related_name='exceptions')
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    message = models.TextField()
    detail = JSONField(default=dict, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    reported_to_gateway = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'gateway_client_exception_report'
        ordering = ['-reported_at']
