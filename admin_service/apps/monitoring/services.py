from .metrics_collector import MetricsCollector, ResourceMonitor
from .alert_manager import AlertManager
from django.utils import timezone
from .models import AlertRule
from apps.userdb.models import ContainerInstance, RouteMetrics
from shared_models.userdb.models import BusinessErrorLog  # 添加缺失的导入
from django.db.models import Avg, Max  

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
        # 3. 检查业务异常
        self.check_business_errors()
        # 新增: 分析资源趋势
        self.analyze_resource_trends()
        # 4. 评估告警规则
        self.alert_manager.check_alerts()
        # 5. 清理历史数据
        self.db_cleaner.cleanup_old_data()

    def check_business_errors(self):
        """检查业务异常并创建告警"""
        # 获取最近30分钟内的未解决异常
        recent_errors = BusinessErrorLog.objects.filter(
            occurred_at__gte=timezone.now() - timezone.timedelta(minutes=30),
            is_resolved=False
        )

        # 按容器实例和异常类型分组统计
        error_groups = recent_errors.values('container_instance', 'error_type').annotate(
            count=models.Count('id')
        )

        for group in error_groups:
            # 检查是否达到告警阈值（5分钟内同一类型异常出现3次）
            if group['count'] >= 3:
                instance = ContainerInstance.objects.get(id=group['container_instance'])
                # 检查是否已存在相同类型的未解决告警
                existing_alert = AlertRule.objects.filter(
                    container_instance=instance,
                    rule_type='business_error',
                    trigger_condition__contains=group['error_type'],
                    is_active=True,
                    triggered_at__gte=timezone.now() - timezone.timedelta(minutes=5)
                ).first()

                if not existing_alert:
                    # 创建新告警
                    AlertRule.objects.create(
                        container_instance=instance,
                        level='error',
                        rule_type='business_error',
                        threshold=3,
                        trigger_condition=f'5分钟内业务异常类型: {group["error_type"]} 出现 {group["count"]} 次',
                        message=f'业务异常告警: {group["error_type"]} 异常频繁发生',
                        is_active=True,
                        triggered_at=timezone.now()
                    )

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

    def analyze_resource_trends(self):
        """分析资源使用趋势并创建告警"""
        # 分析最近1小时的CPU和内存趋势
        one_hour_ago = timezone.now() - timezone.timedelta(hours=1)
        instances = ContainerInstance.objects.filter(is_healthy=True)

        for instance in instances:
            metrics = ContainerMetric.objects.filter(
                container=instance.container,
                timestamp__gte=one_hour_ago
            ).order_by('timestamp')

            if len(metrics) < 5:  # 需要至少5个数据点才能分析趋势
                continue

            # 计算CPU使用率趋势
            cpu_trend = self._calculate_trend([m.cpu_usage for m in metrics])
            memory_trend = self._calculate_trend([m.memory_usage for m in metrics])

            # CPU使用率持续上升且超过阈值
            if cpu_trend > 0.1 and metrics.last().cpu_usage > 80:
                self.alert_manager._trigger_alert(AlertRule.objects.create(
                    container_instance=instance,
                    level='warning',
                    rule_type='cpu_trend',
                    threshold=80,
                    trigger_condition=f'CPU使用率持续上升，当前{metrics.last().cpu_usage}%',
                    message=f'CPU使用率趋势异常: 过去1小时上升{cpu_trend*100:.2f}%',
                    is_active=True,
                    triggered_at=timezone.now()
                ))

            # 内存使用率持续上升且超过阈值
            if memory_trend > 0.1 and metrics.last().memory_usage > 80:
                self.alert_manager._trigger_alert(AlertRule.objects.create(
                    container_instance=instance,
                    level='warning',
                    rule_type='memory_trend',
                    threshold=80,
                    trigger_condition=f'内存使用率持续上升，当前{metrics.last().memory_usage}%',
                    message=f'内存使用率趋势异常: 过去1小时上升{memory_trend*100:.2f}%',
                    is_active=True,
                    triggered_at=timezone.now()
                ))

    def _calculate_trend(self, values):
        """计算数据趋势（简单线性回归斜率）"""
        n = len(values)
        if n < 2:
            return 0

        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = sum(values) / n

        numerator = sum((xi - x_mean) * (yi - y_mean) for xi, yi in zip(x, values))
        denominator = sum((xi - x_mean) **2 for xi in x)

        return numerator / denominator if denominator != 0 else 0