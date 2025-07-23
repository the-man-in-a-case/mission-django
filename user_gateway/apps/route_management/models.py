from django.db import models
from django.utils import timezone

class ContainerHealthRecord(models.Model):
    """容器健康检查记录"""
    container_id = models.CharField(max_length=100, db_index=True)
    service_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=[
        ('healthy', '健康'),
        ('unhealthy', '异常'),
        ('finished', '正常结束')
    ])
    cpu_usage = models.FloatField(null=True, blank=True)
    memory_usage = models.FloatField(null=True, blank=True)
    disk_usage = models.FloatField(null=True, blank=True)
    network_rx = models.BigIntegerField(null=True, blank=True)
    network_tx = models.BigIntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['container_id', '-timestamp']),
            models.Index(fields=['service_name', '-timestamp']),
        ]

class ExceptionData(models.Model):
    """异常数据收集模型"""
    SOURCE_CHOICES = [
        ('redis', 'Redis'),
        ('influxdb', 'InfluxDB'),
    ]
    
    container_id = models.CharField(max_length=100, db_index=True)
    service_name = models.CharField(max_length=100)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    exception_type = models.CharField(max_length=50)
    exception_message = models.TextField()
    stack_trace = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_reported = models.BooleanField(default=False)
    severity = models.CharField(max_length=10, choices=[
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '严重')
    ], default='medium')

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['is_reported', '-timestamp']),
            models.Index(fields=['container_id', '-timestamp']),
        ]

class ServiceRegistry(models.Model):
    """服务注册信息"""
    service_id = models.CharField(max_length=100, unique=True)
    service_type = models.CharField(max_length=50)
    host = models.CharField(max_length=100)
    port = models.IntegerField()
    is_active = models.BooleanField(default=True)
    registered_at = models.DateTimeField(default=timezone.now)
    last_heartbeat = models.DateTimeField(default=timezone.now)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-registered_at']

class MetricsData(models.Model):
    """指标数据"""
    service_id = models.CharField(max_length=100, db_index=True)
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    labels = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['service_id', 'metric_name', '-timestamp']),
        ]
