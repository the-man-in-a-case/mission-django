from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils import timezone

class ServiceInstance(models.Model):
    """服务实例注册信息"""
    service_id = models.CharField(max_length=100, unique=True)
    service_type = models.CharField(max_length=50)
    host = models.CharField(max_length=100)
    port = models.IntegerField()
    health_status = models.CharField(max_length=20, default='healthy')
    registered_at = models.DateTimeField(auto_now_add=True)
    last_health_check = models.DateTimeField(null=True, blank=True)
    health_check_url = models.URLField(null=True, blank=True)
    metadata = JSONField(default=dict, blank=True)

    class Meta:
        db_table = 'gateway_client_service_instance'
        ordering = ['-registered_at']

class ExceptionData(models.Model):
    """异常数据收集模型"""
    SOURCE_CHOICES = [
        ('redis', 'Redis'),
        ('influxdb', 'InfluxDB'),
    ]
    SEVERITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '严重')
    ]
    
    container_id = models.CharField(max_length=100, db_index=True)
    service_name = models.CharField(max_length=100)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    exception_type = models.CharField(max_length=50)
    exception_message = models.TextField()
    stack_trace = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_reported = models.BooleanField(default=False)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default='medium')
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['is_reported', '-timestamp']),
            models.Index(fields=['container_id', '-timestamp']),
        ]

class MetricsData(models.Model):
    """指标数据"""
    service_id = models.CharField(max_length=100, db_index=True)
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    labels = JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['service_id', 'metric_name', '-timestamp']),
        ]
