from django.db import transaction
from django.utils import timezone
from ..userdb.models import User, UserContainer, ContainerInstance
from .k8s_client import K8sClient
from .orchestrator import ContainerOrchestrator

class ContainerService:
    @staticmethod
    @transaction.atomic
    def create_user_container(user_id: str, config: dict) -> UserContainer:
        """创建用户容器（原子操作：K8s部署 + 数据库记录）"""
        user = User.objects.get(id=user_id)
        orchestrator = ContainerOrchestrator()
        
        # 新增：提取MySQL连接配置（假设从用户权限或全局配置获取）
        mysql_config = {
            "host": "mysql-service",  # MySQL服务名（K8s内部DNS）
            "port": "3306",
            "user": "django_user",
            "password": "django_pass"
        }
        
        # 合并数据库配置到容器配置
        extended_config = {
            **config,
            "mysql": mysql_config,
            "port": 8000  # Django应用监听端口（需与Deployment容器端口一致）
        }
        
        # 调用编排器创建K8s资源（需确保orchestrator支持mysql参数）
        deployment_name, service_name = orchestrator.create_k8s_resources(
            user.id, 
            extended_config  # 传递扩展配置
        )
        
        # 创建/更新UserContainer记录
        container = UserContainer.objects.create(
            user=user,
            container_name=f"user-{user_id}-container",
            deployment_name=deployment_name,
            service_name=service_name,
            status='creating',
            **config  # 包含cpu/memory/storage等配置
        )
        
        # 同步容器实例（假设K8s返回Pod信息）
        pods = K8sClient().get_deployment_pods(deployment_name)
        for pod in pods:
            ContainerInstance.objects.create(
                container=container,
                instance_id=pod['id'],
                pod_name=pod['name'],
                pod_ip=pod['ip'],
                port=config.get('port', 8080)
            )
        
        return container

    @staticmethod
    def destroy_user_container(user_id: str) -> bool:
        """销毁用户容器（K8s资源 + 数据库清理）"""
        user = User.objects.get(id=user_id)
        container = UserContainer.objects.get(user=user)
        orchestrator = ContainerOrchestrator()
        
        # 销毁K8s资源
        orchestrator.delete_k8s_resources(container.deployment_name, container.service_name)
        
        # 清理数据库记录
        ContainerInstance.objects.filter(container=container).delete()
        container.delete()
        user.container_id = None
        user.container_status = 'destroyed'
        user.save()
        
        return True

    @staticmethod
    def manage_container(container_id: str, action: str) -> dict:
        """管理容器（启动/停止/重启）"""
        container = UserContainer.objects.get(id=container_id)
        orchestrator = ContainerOrchestrator()
        
        if action == 'start':
            orchestrator.start_deployment(container.deployment_name)
            container.status = 'running'
        elif action == 'stop':
            orchestrator.stop_deployment(container.deployment_name)
            container.status = 'stopped'
        elif action == 'restart':
            orchestrator.restart_deployment(container.deployment_name)
            container.status = 'running'
        
        container.save()
        return {'status': container.status}

    @staticmethod
    def update_container_resources(container_id: str, resource_config: dict) -> bool:
        """更新容器资源配置（CPU/内存/存储）"""
        container = UserContainer.objects.get(id=container_id)
        orchestrator = ContainerOrchestrator()
        
        # 更新K8s部署配置
        orchestrator.update_deployment_resources(container.deployment_name, resource_config)
        
        # 更新数据库记录
        container.cpu_limit = resource_config['cpu_limit']
        container.memory_limit = resource_config['memory_limit']
        container.storage_limit = resource_config['storage_limit']
        container.save()
        
        return True

    @staticmethod
    def get_container_status(container_id: str) -> dict:
        """查询容器实时状态"""
        container = UserContainer.objects.get(id=container_id)
        k8s_client = K8sClient()
        
        # 获取K8s状态
        deployment_status = k8s_client.get_deployment_status(container.deployment_name)
        ready_replicas = deployment_status.get('ready_replicas', 0)
        
        # 更新数据库状态
        container.status = deployment_status.get('phase', 'unknown')
        container.ready_replicas = ready_replicas
        container.save()
        
        return {
            'status': container.status,
            'ready_replicas': ready_replicas,
            'last_updated': container.updated_at.isoformat()
        }