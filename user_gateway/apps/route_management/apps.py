from django.apps import AppConfig


class RouteManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'route_management'
    verbose_name = 'Route Management'

    def ready(self):
        """应用启动时的初始化操作"""
        from .tasks import start_health_checker
        # 启动健康检查任务
        try:
            start_health_checker.delay()
        except Exception:
            # 如果Celery未启动，使用本地调度
            pass