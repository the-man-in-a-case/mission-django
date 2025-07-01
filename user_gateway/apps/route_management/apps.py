from django.apps import AppConfig
from .health_checker import HealthChecker
import logging
import asyncio

logger = logging.getLogger(__name__)

class RouteManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'route_management'
    verbose_name = 'Route Management'

    def ready(self):
        """应用启动时的初始化操作"""
        # 启动健康检查任务
        try:
            from .tasks import start_health_checker
            start_health_checker.delay()
            logger.info("Health check task scheduled via Celery")
        except Exception as e:
            # 如果Celery未启动，使用本地调度
            logger.warning(f"Celery not available, starting local health check: {str(e)}")
            checker = HealthChecker()
            # 在单独线程中运行异步健康检查循环
            import threading
            thread = threading.Thread(target=self._run_health_check, args=(checker,), daemon=True)
            thread.start()

    def _run_health_check(self, checker):
        """在单独线程中运行健康检查"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(checker.start_health_checking())