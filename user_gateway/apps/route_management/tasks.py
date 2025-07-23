import logging
from celery import shared_task
from .services import DataCollectorService
from .health_checker import HealthChecker

logger = logging.getLogger(__name__)

@shared_task
def collect_exceptions_task():
    """收集异常数据的定时任务"""
    collector = DataCollectorService()
    count = collector.collect_all_exceptions()
    logger.info(f"Collected {count} exceptions")
    return count

@shared_task
def report_exceptions_task():
    """上报异常数据的定时任务"""
    collector = DataCollectorService()
    count = collector.report_unreported_exceptions()
    logger.info(f"Reported {count} exceptions")
    return count

@shared_task
def report_metrics_task():
    """上报指标数据的定时任务"""
    # 这里可以添加具体的指标收集逻辑
    logger.info("Metrics reporting task executed")

@shared_task
def start_health_checker():
    """启动健康检查循环"""
    health_checker = HealthChecker()
    health_checker.start_checking()
    logger.info("Health checker started")

# Celery beat配置建议添加到settings.py
CELERY_BEAT_SCHEDULE = {
    'collect-exceptions': {
        'task': 'route_management.tasks.collect_exceptions_task',
        'schedule': 60.0,  # 每分钟收集一次
    },
    'report-exceptions': {
        'task': 'route_management.tasks.report_exceptions_task',
        'schedule': 300.0,  # 每5分钟上报一次
    },
    'report-metrics': {
        'task': 'route_management.tasks.report_metrics_task',
        'schedule': 60.0,  # 每分钟上报一次
    },
    'start-health-checker': {
        'task': 'route_management.tasks.start_health_checker',
        'schedule': 30.0,  # 每30秒检查一次
    },
}