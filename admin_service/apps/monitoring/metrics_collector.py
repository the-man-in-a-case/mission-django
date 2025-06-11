from django.utils import timezone
from userdb.models import ContainerInstance, RouteMetrics, HealthCheckRecord
from .models import MonitoringConfig
import logging

logger = logging.getLogger(__name__)

class MetricsCollector:
    """指标采集器"""
    
    def collect_container_metrics(self):
        """采集容器实例指标"""
        instances = ContainerInstance.objects.all()
        for instance in instances:
            self._update_instance_metrics(instance)
            
    def _update_instance_metrics(self, instance):
        """更新单个实例指标"""
        try:
            # 获取最近5分钟的健康检查记录
            health_checks = HealthCheckRecord.objects.filter(
                container_instance=instance,
                timestamp__gte=timezone.now() - timezone.timedelta(minutes=5)
            )
            
            # 计算健康状态
            success_checks = health_checks.filter(is_healthy=True).count()
            failure_checks = health_checks.filter(is_healthy=False).count()
            
            # 更新实例指标
            instance.is_healthy = success_checks > failure_checks
            instance.consecutive_failures = failure_checks
            instance.current_connections = RouteMetrics.objects.filter(
                route_registry__container=instance.container
            ).aggregate(Sum('current_connections'))['current_connections__sum'] or 0
            
            instance.save()
            logger.info(f"成功更新实例 {instance.instance_id} 指标")
            
        except Exception as e:
            logger.error(f"指标采集失败: {str(e)}")

class ResourceMonitor:
    """资源监控器"""
    
    def check_resource_usage(self):
        """检查资源使用情况"""
        containers = UserContainer.objects.all()
        for container in containers:
            self._check_container_resources(container)
    
    def _check_container_resources(self, container):
        """检查单个容器资源"""
        try:
            # 获取关联实例的资源使用总和
            instances = container.instances.all()
            total_cpu = sum(instance.cpu_usage for instance in instances)
            total_memory = sum(instance.memory_usage for instance in instances)
            
            # 对比资源限制
            cpu_limit = int(container.cpu_limit.replace('m', ''))
            memory_limit = int(container.memory_limit.replace('Gi', '')) * 1024  # 转换为MB
            
            if total_cpu > cpu_limit * 0.9:
                self._trigger_alert(container, 'cpu_overload')
            if total_memory > memory_limit * 0.9:
                self._trigger_alert(container, 'memory_overload')
                
        except Exception as e:
            logger.error(f"资源监控失败: {str(e)}")