from django.db import models
from django.conf import settings

class ServiceInstance(models.Model):
    """用户容器服务实例在网关的注册信息"""
    SERVICE_TYPE_CHOICES = [
        ('business_flow', '业务流程服务'),
        ('data_sync', '数据同步服务'),
    ]
    
    service_id = models.CharField(max_length=64, unique=True, help_text="服务唯一ID（由User ID+服务类型生成）")
    service_type = models.CharField(max_length=32, choices=SERVICE_TYPE_CHOICES)
    host = models.GenericIPAddressField(help_text="容器服务IP地址")
    port = models.IntegerField(help_text="容器服务端口")
    last_heartbeat = models.DateTimeField(auto_now=True, help_text="最后心跳时间")
    is_healthy = models.BooleanField(default=True, help_text="健康状态（由健康检查更新）")

    def __str__(self):
        return f"{self.service_type}-{self.service_id}"

# Create your models here.
