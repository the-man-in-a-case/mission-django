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
        self.db_cleaner = DataCleaner()

    def run_monitoring_cycle(self):
        """执行完整监控周期"""
        # 1. 采集指标
        self.metrics_collector.collect_container_metrics()
        # 2. 检查资源使用
        self.resource_monitor.check_resource_usage()
        # 3. 评估告警规则
        self.alert_manager.check_alerts()
        # 4. 清理历史数据
        self.db_cleaner.cleanup_old_data()

    @staticmethod
    def get_container_dashboard_data(container_id):
        """获取容器监控面板数据"""
        container = UserContainer.objects.get(id=container_id)
        recent_metrics = ContainerMetric.objects.filter(
            container=container,
            timestamp__gte=timezone.now() - timezone.timedelta(hours=24)
        ).order_by('timestamp')

        # 格式化图表数据
        cpu_data = [{'x': m.timestamp.isoformat(), 'y': m.cpu_usage} for m in recent_metrics]
        memory_data = [{'x': m.timestamp.isoformat(), 'y': m.memory_usage} for m in recent_metrics]
        # 其他指标...

        # 获取最近告警
        recent_alerts = ResourceAlert.objects.filter(
            container=container,
            is_resolved=False
        ).order_by('-triggered_at')[:5]

        return {
            'metrics': {
                'cpu': cpu_data,
                'memory': memory_data,
                # 其他指标...
            },
            'alerts': recent_alerts,
            'status': container.status
        }

    @staticmethod
    def get_container_resource_usage(container_id):
        container = UserContainer.objects.get(id=container_id)
        return {
            'cpu_usage': '800m',
            'memory_usage': '1.5Gi',
            'usage_percent': {'cpu': 80, 'memory': 75}
        }