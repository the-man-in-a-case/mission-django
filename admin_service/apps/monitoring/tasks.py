from celery import shared_task
from .services import MonitoringService

@shared_task
def collect_metrics_task():
    """每分钟执行的完整监控周期任务"""
    monitoring_service = MonitoringService()
    monitoring_service.run_monitoring_cycle()  # 执行完整监控周期

@shared_task
def check_alerts_task():
    """每5分钟执行的警报检查任务"""
    MonitoringService().alert_manager.check_alerts()