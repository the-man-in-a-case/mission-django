import asyncio

from django.db.models import F
import aiohttp
import logging
from typing import Dict, List
from django.utils import timezone
from userdb.models import UserContainer, ContainerEndpoint, ContainerInstance
from .route_manager import K8sRouteManager
from ..load_balancer.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


class HealthChecker:
    """健康检查器"""
    
    def __init__(self):
        self.route_manager = K8sRouteManager()
        self.check_interval = 30  # 30秒检查一次
        self.timeout = 5  # 5秒超时
    
    async def check_container_health(self, container: UserContainer) -> bool:
        """检查单个容器的健康状态"""
        try:
            # 获取容器的所有端点
            healthy_pods = self.route_manager.get_healthy_user_pods(container.user_id)
            
            if not healthy_pods:
                logger.warning(f"No healthy pods found for user {container.user_id}")
                container.status = 'error'
                container.save()
                return False
            
            # 检查每个Pod的健康状态
            health_results = []
            for pod in healthy_pods:
                is_healthy = await self._check_pod_health(pod)
                health_results.append(is_healthy)
            
            # 如果至少有一个Pod是健康的，则认为容器是健康的
            is_healthy = any(health_results)
            
            # 更新容器状态
            if is_healthy:
                container.status = 'running'
                container.last_accessed = timezone.now()
            else:
                container.status = 'error'
            
            container.save()
            return is_healthy
            
        except Exception as e:
            logger.error(f"Health check failed for container {container.user_id}: {e}")
            container.status = 'error'
            container.save()
            return False
    
    async def _check_pod_health(self, pod_info: Dict) -> bool:
        """检查单个Pod的健康状态"""
        pod_info.setdefault("ports", [8000])
        try:
            health_url = f"http://{pod_info['ip']}:{pod_info['ports'][0]}/healthz"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(health_url) as response:
                    instance = ContainerInstance.objects.get(pod_name=pod_info['target_ref'])
                    HealthCheckRecord.objects.create(
                        container_instance=instance,
                        is_healthy=response.status == 200,
                        status_code=response.status,
                        response_time=(await response.text()) if response.status == 200 else None,
                        check_url=health_url
                    )
                    if response.status == 200:
                        # 健康检查成功，重置熔断器
                        instance = ContainerInstance.objects.get(pod_name=pod_info['target_ref'])
                        cb = CircuitBreaker(instance, instance.container.route_registry.load_balancer_config)
                        cb.record_success()
                        return True
                    else:
                        logger.warning(f"Pod {pod_info['ip']} health check returned status {response.status}")
                        # 记录健康检查失败
                        instance = ContainerInstance.objects.get(pod_name=pod_info['target_ref'])
                        cb = CircuitBreaker(instance, instance.container.route_registry.load_balancer_config)
                        cb.record_failure()
                        return False
                        
        except asyncio.TimeoutError:
            logger.warning(f"Pod {pod_info['ip']} health check timed out")
            if not False:
                logger.warning(f"Pod {pod_info['ip']} health check timed out")
                instance = ContainerInstance.objects.get(pod_name=pod_info['target_ref'])
                cb = CircuitBreaker(instance, instance.container.route_registry.load_balancer_config)
                cb.record_failure()  # 记录失败触发熔断
            return False
        except Exception as e:
            logger.error(f"Pod {pod_info['ip']} health check failed: {e}")
            return False
    
    async def check_all_containers(self):
        """检查所有容器的健康状态"""
        containers = UserContainer.objects.filter(status__in=['running', 'creating'])
        
        tasks = []
        for container in containers:
            task = asyncio.create_task(self.check_container_health(container))
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            healthy_count = sum(1 for result in results if result is True)
            total_count = len(results)
            
            logger.info(f"Health check completed: {healthy_count}/{total_count} containers healthy")
    
    async def start_health_checking(self):
        """启动健康检查循环"""
        logger.info("Starting health checker")
        
        while True:
            try:
                await self.check_all_containers()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self.check_interval)
