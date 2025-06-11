from .metrics_collector import MetricsCollector, ResourceMonitor
from .alert_manager import AlertManager
from django.utils import timezone
from .models import AlertRule
from apps.userdb.models import ContainerInstance, RouteMetrics

class MonitoringService:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.resource_monitor = ResourceMonitor()
        self.alert_manager = AlertManager()

    @staticmethod
    def get_container_resource_usage(container_id):
        container = UserContainer.objects.get(id=container_id)
        return {
            'cpu_usage': '800m',
            'memory_usage': '1.5Gi',
            'usage_percent': {'cpu': 80, 'memory': 75}
        }

    def run_monitoring_cycle(self):
        """执行完整监控周期"""
        self.metrics_collector.collect_container_metrics()
        self.resource_monitor.check_resource_usage()
        self.alert_manager.check_alerts()
        self._cleanup_old_data()

    def _cleanup_old_data(self):
        """清理7天前的监控数据"""
        cutoff = timezone.now() - timezone.timedelta(days=7)
        RouteMetrics.objects.filter(updated_at__lt=cutoff).delete()
        AlertRule.objects.filter(is_active=False, updated_at__lt=cutoff).delete()