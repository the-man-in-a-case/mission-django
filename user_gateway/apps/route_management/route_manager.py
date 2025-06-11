import logging
import json
import asyncio
from typing import Dict, List, Optional, Tuple
from kubernetes import client, config
from kubernetes.client.exceptions import ApiException
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from userdb.models import UserContainer, ContainerEndpoint, RouteCache
from .registry import ContainerRegistry

logger = logging.getLogger(__name__)


class K8sRouteManager:
    """基于Kubernetes的路由管理器"""
    
    def __init__(self):
        try:
            # 尝试加载集群内配置
            config.load_incluster_config()
        except config.ConfigException:
            # 如果不在集群内，加载本地配置
            config.load_kube_config()
        
        self.k8s_client = client.CoreV1Api()
        self.apps_client = client.AppsV1Api()
        self.autoscaling_client = client.AutoscalingV2Api()
        self.networking_client = client.NetworkingV1Api()
        
        self.registry = ContainerRegistry()
        self.namespace = settings.USER_CONTAINER_NAMESPACE
        self.admin_service_url = settings.ADMIN_SERVICE_URL
        
    def get_user_container_service(self, user_id: str) -> Optional[Dict]:
        """通过Kubernetes Service发现用户容器"""
        service_name = f"user-{user_id}-service"
        
        try:
            service = self.k8s_client.read_namespaced_service(
                name=service_name, 
                namespace=self.namespace
            )
            
            service_info = {
                'cluster_ip': service.spec.cluster_ip,
                'ports': [{'port': port.port, 'target_port': port.target_port} for port in service.spec.ports],
                'selector': service.spec.selector,
                'service_name': service_name,
                'namespace': self.namespace
            }
            
            # 更新注册表
            self.registry.register_container(user_id, {
                'service_name': service_name,
                'cluster_ip': service.spec.cluster_ip,
                'port': service.spec.ports[0].port if service.spec.ports else 80,
                'namespace': self.namespace,
                'deployment_name': f"user-{user_id}",
                'status': 'running'
            })
            
            return service_info
            
        except ApiException as e:
            if e.status == 404:
                logger.info(f"Service not found for user {user_id}")
                return None
            logger.error(f"Error getting service for user {user_id}: {e}")
            raise
    
    def get_healthy_user_pods(self, user_id: str) -> List[Dict]:
        """获取用户的健康Pod列表"""
        service_name = f"user-{user_id}-service"
        
        try:
            endpoints = self.k8s_client.read_namespaced_endpoints(
                name=service_name, 
                namespace=self.namespace
            )
            
            healthy_pods = []
            if endpoints.subsets:
                for subset in endpoints.subsets:
                    if subset.addresses:  # ready的Pod
                        for address in subset.addresses:
                            pod_info = {
                                'ip': address.ip,
                                'ports': [port.port for port in subset.ports] if subset.ports else [80],
                                'target_ref': address.target_ref.name if address.target_ref else None
                            }
                            healthy_pods.append(pod_info)
                            
                            # 更新数据库中的端点信息
                            self._update_endpoint_info(user_id, pod_info)
            
            return healthy_pods
            
        except ApiException as e:
            if e.status == 404:
                logger.info(f"Endpoints not found for user {user_id}")
                return []
            logger.error(f"Error getting endpoints for user {user_id}: {e}")
            return []
    
    def _update_endpoint_info(self, user_id: str, pod_info: Dict):
        """更新端点信息到数据库"""
        try:
            container = UserContainer.objects.get(user_id=user_id)
            endpoint, created = ContainerEndpoint.objects.get_or_create(
                container=container,
                pod_name=pod_info.get('target_ref', f"pod-{pod_info['ip']}"),
                defaults={
                    'pod_ip': pod_info['ip'],
                    'port': pod_info['ports'][0] if pod_info['ports'] else 80,
                    'is_ready': True,
                    'last_health_check': timezone.now()
                }
            )
            
            if not created:
                endpoint.pod_ip = pod_info['ip']
                endpoint.port = pod_info['ports'][0] if pod_info['ports'] else 80
                endpoint.is_ready = True
                endpoint.last_health_check = timezone.now()
                endpoint.save()
                
        except UserContainer.DoesNotExist:
            logger.warning(f"Container not found for user {user_id}")
    
    def route_request(self, user_id: str, request_data: Dict) -> Tuple[Optional[str], Dict]:
        """基于K8s Service进行路由"""
        try:
            # 首先检查缓存
            cached_route = self._get_cached_route(user_id)
            if cached_route and self._verify_route_health(cached_route):
                return cached_route['target_url'], cached_route
            
            # 从K8s API获取服务信息
            service_info = self.get_user_container_service(user_id)
            
            if not service_info:
                # 触发容器创建
                self._trigger_container_creation(user_id)
                return None, {'status': 'creating', 'message': 'Container is being created'}
            
            # 构建目标URL
            target_url = f"http://{service_info['cluster_ip']}:{service_info['ports'][0]['port']}"
            
            # 缓存路由信息
            route_info = {
                'target_url': target_url,
                'service_info': service_info,
                'cached_at': timezone.now().isoformat()
            }
            self._cache_route(user_id, route_info)
            
            return target_url, route_info
            
        except Exception as e:
            logger.error(f"Route request failed for user {user_id}: {e}")
            return None, {'status': 'error', 'message': str(e)}
    
    def _get_cached_route(self, user_id: str) -> Optional[Dict]:
        """从缓存获取路由信息"""
        try:
            route_cache = RouteCache.objects.get(user_id=user_id)
            if not route_cache.is_expired():
                return route_cache.route_data
            else:
                route_cache.delete()
                return None
        except RouteCache.DoesNotExist:
            return None
    
    def _cache_route(self, user_id: str, route_info: Dict):
        """缓存路由信息"""
        expires_at = timezone.now() + timezone.timedelta(minutes=5)
        RouteCache.objects.update_or_create(
            user_id=user_id,
            defaults={
                'route_data': route_info,
                'expires_at': expires_at
            }
        )
    
    def _verify_route_health(self, route_info: Dict) -> bool:
        """验证路由健康状态"""
        try:
            # 简单的健康检查逻辑
            service_info = route_info.get('service_info', {})
            if not service_info.get('cluster_ip'):
                return False
            
            # 可以添加更复杂的健康检查逻辑
            return True
        except Exception as e:
            logger.error(f"Route health check failed: {e}")
            return False
    
    def _trigger_container_creation(self, user_id: str):
        """触发容器创建"""
        try:
            # 可以直接在这里创建容器，或者通知Admin Service
            if settings.ENABLE_DIRECT_CONTAINER_CREATION:
                self.create_user_deployment(user_id)
            else:
                self._notify_admin_service(user_id)
        except Exception as e:
            logger.error(f"Failed to trigger container creation for user {user_id}: {e}")
    
    def create_user_deployment(self, user_id: str):
        """创建用户的Kubernetes Deployment和Service"""
        try:
            # 创建Deployment
            deployment = self._build_deployment_spec(user_id)
            self.apps_client.create_namespaced_deployment(
                namespace=self.namespace, 
                body=deployment
            )
            
            # 创建Service
            service = self._build_service_spec(user_id)
            self.k8s_client.create_namespaced_service(
                namespace=self.namespace, 
                body=service
            )
            
            # 创建HPA
            hpa = self._build_hpa_spec(user_id)
            self.autoscaling_client.create_namespaced_horizontal_pod_autoscaler(
                namespace=self.namespace,
                body=hpa
            )
            
            logger.info(f"Created deployment and service for user {user_id}")
            
        except ApiException as e:
            logger.error(f"Failed to create deployment for user {user_id}: {e}")
            raise
    
    def _build_deployment_spec(self, user_id: str) -> client.V1Deployment:
        """构建Deployment规格"""
        return client.V1Deployment(
            metadata=client.V1ObjectMeta(
                name=f"user-{user_id}",
                namespace=self.namespace,
                labels={"app": f"user-{user_id}", "user-id": str(user_id), "managed-by": "user-gateway"}
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={"app": f"user-{user_id}"}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": f"user-{user_id}", "user-id": str(user_id)}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=f"user-{user_id}-container",
                                image=settings.USER_CONTAINER_IMAGE,
                                ports=[client.V1ContainerPort(container_port=8080)],
                                env=[
                                    client.V1EnvVar(name="USER_ID", value=str(user_id)),
                                    client.V1EnvVar(name="DB_NAME", value=f"user_{user_id}_db"),
                                    client.V1EnvVar(name="GATEWAY_URL", value=settings.GATEWAY_URL)
                                ],
                                resources=client.V1ResourceRequirements(
                                    requests={"cpu": "500m", "memory": "1Gi"},
                                    limits={"cpu": "1000m", "memory": "2Gi"}
                                ),
                                readiness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(
                                        path="/health",
                                        port=8080
                                    ),
                                    initial_delay_seconds=10,
                                    period_seconds=5
                                ),
                                liveness_probe=client.V1Probe(
                                    http_get=client.V1HTTPGetAction(
                                        path="/health",
                                        port=8080
                                    ),
                                    initial_delay_seconds=30,
                                    period_seconds=10
                                )
                            )
                        ]
                    )
                )
            )
        )
    
    def _build_service_spec(self, user_id: str) -> client.V1Service:
        """构建Service规格"""
        return client.V1Service(
            metadata=client.V1ObjectMeta(
                name=f"user-{user_id}-service",
                namespace=self.namespace,
                labels={"app": f"user-{user_id}", "user-id": str(user_id)}
            ),
            spec=client.V1ServiceSpec(
                selector={"app": f"user-{user_id}"},
                ports=[client.V1ServicePort(
                    port=80, 
                    target_port=8080,
                    protocol="TCP"
                )],
                type="ClusterIP"
            )
        )
    
    def _build_hpa_spec(self, user_id: str) -> client.V2HorizontalPodAutoscaler:
        """构建HPA规格"""
        return client.V2HorizontalPodAutoscaler(
            metadata=client.V1ObjectMeta(
                name=f"user-{user_id}-hpa",
                namespace=self.namespace
            ),
            spec=client.V2HorizontalPodAutoscalerSpec(
                scale_target_ref=client.V2CrossVersionObjectReference(
                    api_version="apps/v1",
                    kind="Deployment",
                    name=f"user-{user_id}"
                ),
                min_replicas=1,
                max_replicas=3,
                metrics=[
                    client.V2MetricSpec(
                        type="Resource",
                        resource=client.V2ResourceMetricSource(
                            name="cpu",
                            target=client.V2MetricTarget(
                                type="Utilization",
                                average_utilization=70
                            )
                        )
                    )
                ]
            )
        )
    
    def _notify_admin_service(self, user_id: str):
        """通知Admin Service创建容器"""
        # 这里可以实现异步通知Admin Service的逻辑
        # 比如发送消息到消息队列，或者直接调用Admin Service API
        pass
    
    def delete_user_resources(self, user_id: str):
        """删除用户相关的K8s资源"""
        try:
            # 删除HPA
            try:
                self.autoscaling_client.delete_namespaced_horizontal_pod_autoscaler(
                    name=f"user-{user_id}-hpa",
                    namespace=self.namespace
                )
            except ApiException as e:
                if e.status != 404:
                    logger.error(f"Failed to delete HPA for user {user_id}: {e}")
            
            # 删除Service
            try:
                self.k8s_client.delete_namespaced_service(
                    name=f"user-{user_id}-service",
                    namespace=self.namespace
                )
            except ApiException as e:
                if e.status != 404:
                    logger.error(f"Failed to delete Service for user {user_id}: {e}")
            
            # 删除Deployment
            try:
                self.apps_client.delete_namespaced_deployment(
                    name=f"user-{user_id}",
                    namespace=self.namespace
                )
            except ApiException as e:
                if e.status != 404:
                    logger.error(f"Failed to delete Deployment for user {user_id}: {e}")
            
            # 从注册表中移除
            self.registry.unregister_container(user_id)
            
            # 删除数据库记录
            UserContainer.objects.filter(user_id=user_id).delete()
            
            logger.info(f"Deleted all resources for user {user_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete resources for user {user_id}: {e}")
            raise

    def _select_instance_by_response_time(self, user_id: str) -> Optional[Dict]:
            """基于响应时间选择最优容器实例（借鉴现有健康检查和端点获取逻辑）"""
            # 从数据库获取容器实例的响应时间指标（参考RouteLog模型的response_time字段）
            instances = ContainerInstance.objects.filter(
                container__user_id=user_id,
                status='running',
                is_healthy=True
            ).order_by('current_connections', 'avg_response_time')  # 优先最少连接+最短响应时间

            if instances:
                return {
                    'ip': instances[0].pod_ip,
                    'port': instances[0].port,
                    'instance_id': instances[0].instance_id
                }
            return None