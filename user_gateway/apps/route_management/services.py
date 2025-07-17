import logging
import asyncio
from typing import Dict, Optional, Tuple
from django.conf import settings
from django.utils import timezone
from .models import UserContainer, RouteMetrics
from .route_manager import K8sRouteManager
from .health_checker import HealthChecker
from .registry import ContainerRegistry
from apps.userdb.models import MonitorEvent, ContainerInstance  

logger = logging.getLogger(__name__)

class RouteManagementService:
    @staticmethod
    def report_container_status(message: str, instance: ContainerInstance, detail: Optional[Dict] = None, level: str = 'info'):
        """上报容器状态到监控表"""
        try:
            MonitorEvent.objects.create(
                event_type='container',
                source='route_management',
                level=level,
                message=message,
                detail=detail or {
                    'instance_id': instance.instance_id,
                    'pod_name': instance.pod_name,
                    'container_id': instance.container.id,
                    'status': instance.status
                }
            )
            logger.info(f"容器状态上报成功: {message}")
            return True
        except Exception as e:
            logger.error(f"容器状态上报失败: {str(e)}")
            return False

    @staticmethod
    def collect_container_resources(instance: ContainerInstance) -> Dict:
        """采集容器资源使用情况"""
        try:
            # 从K8s API获取资源使用数据
            route_manager = K8sRouteManager()
            pod_metrics = route_manager.get_pod_metrics(instance.pod_name, instance.container.namespace)

            # 提取CPU和内存使用
            resources = {
                'cpu_usage': pod_metrics.get('cpu_usage', '0m'),
                'memory_usage': pod_metrics.get('memory_usage', '0Mi'),
                'restart_count': pod_metrics.get('restart_count', 0),
                'timestamp': timezone.now().isoformat()
            }

            # 上报资源状态
            RouteManagementService.report_container_status(
                message=f"容器资源使用情况: CPU {resources['cpu_usage']}, 内存 {resources['memory_usage']}",
                instance=instance,
                detail=resources,
                level='info'
            )

            return resources
        except Exception as e:
            logger.error(f"容器资源采集失败: {str(e)}")
            return {}