from celery import shared_task
from .health_checker import HealthChecker
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def start_health_checker(self):
    """启动健康检查Celery任务"""
    try:
        checker = HealthChecker()
        logger.info("Starting health check loop via Celery")
        # 使用异步方式运行健康检查循环
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(checker.start_health_checking())
    except Exception as e:
        logger.error(f"Health checker task failed: {str(e)}")
        self.retry(exc=e, countdown=60)