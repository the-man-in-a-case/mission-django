
import redis
import json
import logging
from typing import Dict, List, Optional
from django.conf import settings
from django.utils import timezone
from userdb.models import UserContainer, ContainerEndpoint

logger = logging.getLogger(__name__)


class ContainerRegistry:
    """容器注册表管理"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        self.registry_prefix = "container_registry"
        self.cache_ttl = 300  # 5分钟
    
    def register_container(self, user_id: str, container_info: Dict):
        """注册容器信息"""
        try:
            # 更新数据库
            container, created = UserContainer.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'deployment_name': container_info.get('deployment_name'),
                    'service_name': container_info.get('service_name'),
                    'namespace': container_info.get('namespace', 'user-containers'),
                    'cluster_ip': container_info.get('cluster_ip'),
                    'port': container_info.get('port', 80),
                    'status': 'running',
                    'replica_count': container_info.get('replica_count', 1)
                }
            )
            
            if not created:
                container.cluster_ip = container_info.get('cluster_ip')
                container.port = container_info.get('port', 80)
                container.status = 'running'
                container.replica_count = container_info.get('replica_count', 1)
                container.save()
            
            # 更新Redis缓存
            cache_key = f"{self.registry_prefix}:{user_id}"
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(container_info)
            )
            
            logger.info(f"Container registered for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register container for user {user_id}: {e}")
            return False
    
    def unregister_container(self, user_id: str):
        """注销容器"""
        try:
            # 更新数据库状态
            UserContainer.objects.filter(user_id=user_id).update(
                status='terminating',
                updated_at=timezone.now()
            )
            
            # 从Redis缓存中删除
            cache_key = f"{self.registry_prefix}:{user_id}"
            self.redis_client.delete(cache_key)
            
            logger.info(f"Container unregistered for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister container for user {user_id}: {e}")
            return False
    
    def get_container_info(self, user_id: str) -> Optional[Dict]:
        """获取容器信息"""
        # 先从Redis缓存获取
        cache_key = f"{self.registry_prefix}:{user_id}"
        cached_info = self.redis_client.get(cache_key)
        
        if cached_info:
            return json.loads(cached_info)
        
        # 从数据库获取
        try:
            container = UserContainer.objects.get(user_id=user_id)
            container_info = {
                'deployment_name': container.deployment_name,
                'service_name': container.service_name,
                'namespace': container.namespace,
                'cluster_ip': container.cluster_ip,
                'port': container.port,
                'status': container.status,
                'replica_count': container.replica_count
            }
            
            # 回写到Redis
            self.redis_client.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(container_info)
            )
            
            return container_info
            
        except UserContainer.DoesNotExist:
            return None
    
    def get_all_containers(self) -> List[Dict]:
        """获取所有容器信息"""
        containers = UserContainer.objects.filter(status__in=['running', 'creating'])
        return [
            {
                'user_id': container.user_id,
                'deployment_name': container.deployment_name,
                'service_name': container.service_name,
                'namespace': container.namespace,
                'cluster_ip': container.cluster_ip,
                'port': container.port,
                'status': container.status,
                'replica_count': container.replica_count
            }
            for container in containers
        ]

