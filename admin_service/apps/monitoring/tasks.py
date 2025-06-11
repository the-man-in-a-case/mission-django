from celery import shared_task
from .services import MonitoringService

@shared_task
def collect_metrics_task():
    """每分钟执行的指标采集任务"""
    MonitoringService().metrics_collector.collect_container_metrics()

@shared_task
def check_alerts_task():
    """每5分钟执行的警报检查任务"""
    MonitoringService().alert_manager.check_alerts()