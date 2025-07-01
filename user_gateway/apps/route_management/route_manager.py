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
        
    def get_user_container_service(self, tenant_id: str) -> Optional[Dict]:
        """通过Kubernetes Service发现用户容器"""
        service_name = f"user-container-svc-{tenant_id}"
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
            self.registry.register_container(tenant_id, {
                'service_name': service_name,
                'cluster_ip': service.spec.cluster_ip,
                'port': service.spec.ports[0].port if service.spec.ports else 80,
                'namespace': self.namespace,
                'deployment_name': f"user-container-dep-{tenant_id}",
                # 修正状态值为Kubernetes标准格式（首字母大写）
                'status': 'Running'
            })
            return service_info
        except ApiException as e:
            if e.status == 404:
                logger.info(f"Service not found for tenant {tenant_id}")
                return None
            logger.error(f"Error getting service for tenant {tenant_id}: {e}")
            raise
    
    def get_healthy_user_pods(self, tenant_id: str) -> List[Dict]:
        """获取用户的健康Pod列表"""
        service_name = f"user-container-svc-{tenant_id}"
        try:
            endpoints = self.k8s_client.read_namespaced_endpoints(
                name=service_name, 
                namespace=self.namespace
            )
            healthy_pods = []
            if endpoints.subsets:
                for subset in endpoints.subsets:
                    if subset.addresses:
                        for address in subset.addresses:
                            pod_info = {
                                'ip': address.ip,
                                'ports': [port.port for port in subset.ports] if subset.ports else [80],
                                'target_ref': address.target_ref.name if address.target_ref else None
                            }
                            healthy_pods.append(pod_info)
                            self._update_endpoint_info(tenant_id, pod_info)
            return healthy_pods
        except ApiException as e:
            if e.status == 404:
                logger.info(f"Endpoints not found for tenant {tenant_id}")
                return []
            logger.error(f"Error getting endpoints for tenant {tenant_id}: {e}")
            return []
    
    def _update_endpoint_info(self, tenant_id: str, pod_info: Dict):
        """更新端点信息到数据库"""
        try:
            container = UserContainer.objects.get(user_id=tenant_id)
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
            logger.warning(f"Container not found for tenant {tenant_id}")
    
    def route_request(self, tenant_id: str, request_data: Dict) -> Tuple[Optional[str], Dict]:
        """基于K8s Service进行路由"""
        import time
        import uuid
        from ..load_balancer.models import RouteRegistry, RouteLog
        start_time = time.time()
        request_id = request_data.get('request_id', str(uuid.uuid4()))
        client_ip = request_data.get('client_ip', 'unknown')
        request_method = request_data.get('method', 'GET')
        request_path = request_data.get('path', '/')
        user_agent = request_data.get('user_agent', '')
        headers = request_data.get('headers', {})
        target_url = None
        route_info = {}
        success = False
        response_time = 0
        response_status = 0
        error_type = None
        error_message = None
        try:
            cached_route = self._get_cached_route(tenant_id)
            if cached_route and self._verify_route_health(cached_route):
                target_url = cached_route['target_url']
                route_info = cached_route
                success = True
                response_time = (time.time() - start_time) * 1000
                response_status = 200
                error_type = None
                error_message = None
                return target_url, route_info
            
            service_info = self.get_user_container_service(tenant_id)
            if not service_info:
                self._trigger_container_creation(tenant_id)
                success = False
                response_time = (time.time() - start_time) * 1000
                response_status = 503
                error_type = 'gateway'
                error_message = 'Container is being created'
                return None, {'status': 'creating', 'message': 'Container is being created'}
            
            target_url = f"http://{service_info['cluster_ip']}:{service_info['ports'][0]['port']}"
            route_info = {
                'target_url': target_url,
                'service_info': service_info,
                'cached_at': timezone.now().isoformat()
            }
            self._cache_route(tenant_id, route_info)
            
            success = True
            response_time = (time.time() - start_time) * 1000
            response_status = 200
            error_type = None
            error_message = None
            
            return target_url, route_info
        
        except Exception as e:
            logger.error(f"Route request failed for tenant {tenant_id}: {e}")
            success = False
            response_time = (time.time() - start_time) * 1000
            response_status = 500
            error_type = 'server'
            error_message = str(e)
            return None, {'status': 'error', 'message': str(e)}
        
        finally:
            # 记录路由日志
            try:
                from userdb.models import UserContainer
                container = UserContainer.objects.get(user_id=tenant_id)
                route_registry = RouteRegistry.objects.get(container=container)

                RouteLog.objects.create(
                    route_registry=route_registry,
                    request_id=request_id,
                    request_method=request_method,
                    request_path=request_path,
                    request_headers=headers,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    target_url=target_url,
                    load_balance_strategy=route_registry.load_balance_strategy,
                    response_status=response_status,
                    response_time=response_time,
                    error_type=error_type,
                    error_message=error_message
                )

                # 更新路由指标
                if hasattr(route_registry, 'metrics'):
                    route_registry.metrics.update_metrics(
                        response_time=response_time,
                        success=success,
                        error_type=error_type
                    )

            except UserContainer.DoesNotExist:
                logger.warning(f"Container not found for tenant {tenant_id}, cannot log route")
            except RouteRegistry.DoesNotExist:
                logger.warning(f"Route registry not found for tenant {tenant_id}, cannot log route")
            except Exception as e:
                logger.error(f"Failed to log route request: {str(e)}")

        return target_url, route_info
    
    def _get_cached_route(self, tenant_id: str) -> Optional[Dict]:
        """从缓存获取路由信息"""
        try:
            route_cache = RouteCache.objects.get(user_id=tenant_id)
            if not route_cache.is_expired():
                return route_cache.route_data
            else:
                route_cache.delete()
                return None
        except RouteCache.DoesNotExist:
            return None
    
    def _cache_route(self, tenant_id: str, route_info: Dict):
        """优化的路由缓存策略"""
        # 从配置读取缓存TTL，默认为5分钟
        ttl_minutes = getattr(settings, 'ROUTE_CACHE_TTL', 5)
        expires_at = timezone.now() + timezone.timedelta(minutes=ttl_minutes)
        
        # 添加缓存版本控制
        route_info['cache_version'] = 'v2'
        
        RouteCache.objects.update_or_create(
            user_id=tenant_id,
            defaults={
                'route_data': route_info,
                'expires_at': expires_at,
                # 添加缓存命中率跟踪
                'hit_count': 0
            }
        )
    
    def _verify_route_health(self, route_info: Dict) -> bool:
        """增强的路由健康检查逻辑"""
        try:
            service_info = route_info.get('service_info', {})
            cluster_ip = service_info.get('cluster_ip')
            port = service_info['ports'][0]['port'] if service_info.get('ports') else 80
            
            if not cluster_ip:
                return False
            
            # 多维度健康检查
            health_checks = [
                self._check_http_health(f"http://{cluster_ip}:{port}/health"),
                self._check_tcp_health(cluster_ip, port),
                self._check_latency(f"http://{cluster_ip}:{port}/ping")
            ]
            
            # 至少2项检查通过才算健康
            return sum(health_checks) >= 2
        except Exception as e:
            logger.error(f"Route health check failed: {e}")
            return False
    
    def _check_http_health(self, url: str) -> bool:
        """HTTP健康检查"""
        try:
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _check_tcp_health(self, host: str, port: int) -> bool:
        """TCP端口检查"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                return s.connect_ex((host, port)) == 0
        except:
            return False
    
    def _check_latency(self, url: str) -> bool:
        """响应延迟检查"""
        try:
            start_time = time.time()
            requests.get(url, timeout=1)
            latency = (time.time() - start_time) * 1000  # 转换为毫秒
            return latency < 300  # 延迟小于300ms
        except:
            return False
    
    def _trigger_container_creation(self, tenant_id: str):
        """触发容器创建"""
        try:
            # 可以直接在这里创建容器，或者通知Admin Service
            if settings.ENABLE_DIRECT_CONTAINER_CREATION:
                self.create_user_deployment(tenant_id)
            else:
                self._notify_admin_service(tenant_id)
        except Exception as e:
            logger.error(f"Failed to trigger container creation for tenant {tenant_id}: {e}")
    
    def create_user_deployment(self, tenant_id: str):
        """创建用户的Kubernetes Deployment和Service"""
        try:
            # 创建Deployment
            deployment = self._build_deployment_spec(tenant_id)
            self.apps_client.create_namespaced_deployment(
                namespace=self.namespace, 
                body=deployment
            )
            
            # 创建Service
            service = self._build_service_spec(tenant_id)
            self.k8s_client.create_namespaced_service(
                namespace=self.namespace, 
                body=service
            )
            
            # 创建HPA
            hpa = self._build_hpa_spec(tenant_id)
            self.autoscaling_client.create_namespaced_horizontal_pod_autoscaler(
                namespace=self.namespace,
                body=hpa
            )
            
            logger.info(f"Created deployment and service for tenant {tenant_id}")
            
        except ApiException as e:
            logger.error(f"Failed to create deployment for tenant {tenant_id}: {e}")
            raise
    
    def _build_deployment_spec(self, tenant_id: str) -> client.V1Deployment:
        """构建Deployment规格"""
        return client.V1Deployment(
            metadata=client.V1ObjectMeta(
                # 统一Deployment命名规范
                name=f"user-container-dep-{tenant_id}",
                namespace=self.namespace,
                labels={"app": "user-container", "tenant": str(tenant_id), "managed-by": "user-gateway"}
            ),
            spec=client.V1DeploymentSpec(
                replicas=1,
                selector=client.V1LabelSelector(
                    match_labels={"app": "user-container", "tenant": str(tenant_id)}
                ),
                template=client.V1PodTemplateSpec(
                    metadata=client.V1ObjectMeta(
                        labels={"app": "user-container", "tenant": str(tenant_id)}
                    ),
                    spec=client.V1PodSpec(
                        containers=[
                            client.V1Container(
                                name=f"user-container-{tenant_id}",
                                image=settings.USER_CONTAINER_IMAGE,
                                ports=[client.V1ContainerPort(container_port=8080)],
                                env=[
                                    client.V1EnvVar(name="USER_ID", value=str(tenant_id)),
                                    # 添加TENANT_ID环境变量，确保与tenant_id一致
                                    client.V1EnvVar(name="TENANT_ID", value=str(tenant_id)),
                                    client.V1EnvVar(name="DB_NAME", value=f"user_{tenant_id}_db"),
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
    
    def _build_service_spec(self, tenant_id: str) -> client.V1Service:
        """构建Service规格"""
        return client.V1Service(
            metadata=client.V1ObjectMeta(
                name=f"user-container-svc-{tenant_id}",
                namespace=self.namespace,
                labels={"app": f"user-{tenant_id}", "user-id": str(tenant_id)}
            ),
            spec=client.V1ServiceSpec(
                selector={"app": f"user-{tenant_id}"},
                ports=[client.V1ServicePort(
                    port=80, 
                    target_port=8080,
                    protocol="TCP"
                )],
                type="ClusterIP"
            )
        )
    
    def _build_hpa_spec(self, tenant_id: str) -> client.V2HorizontalPodAutoscaler:
        """构建HPA规格"""
        return client.V2HorizontalPodAutoscaler(
            metadata=client.V1ObjectMeta(
                name=f"user-{tenant_id}-hpa",
                namespace=self.namespace
            ),
            spec=client.V2HorizontalPodAutoscalerSpec(
                scale_target_ref=client.V2CrossVersionObjectReference(
                    api_version="apps/v1",
                    kind="Deployment",
                    name=f"user-{tenant_id}"
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
    
    def _notify_admin_service(self, tenant_id: str):
        """通知Admin Service创建容器"""
        try:
            import requests
            from django.conf import settings
            
            payload = {
                'tenant_id': tenant_id,
                'status': 'creating',
                'timestamp': timezone.now().isoformat()
            }
            
            response = requests.post(
                f"{settings.ADMIN_SERVICE_URL}/api/containers/notify",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully notified admin service for tenant {tenant_id}")
            else:
                logger.warning(f"Admin service notification failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to notify admin service: {e}")
    
    def delete_user_resources(self, tenant_id: str):
        """删除用户相关的K8s资源"""
        try:
            # 删除HPA
            try:
                self.autoscaling_client.delete_namespaced_horizontal_pod_autoscaler(
                    name=f"user-{tenant_id}-hpa",
                    namespace=self.namespace
                )
            except ApiException as e:
                if e.status != 404:
                    logger.error(f"Failed to delete HPA for tenant {tenant_id}: {e}")
            
            # 删除Service
            try:
                self.k8s_client.delete_namespaced_service(
                    name=f"user-container-svc-{tenant_id}",
                    namespace=self.namespace
                )
            except ApiException as e:
                if e.status != 404:
                    logger.error(f"Failed to delete Service for tenant {tenant_id}: {e}")
            
            # 删除Deployment
            try:
                self.apps_client.delete_namespaced_deployment(
                    name=f"user-container-dep-{tenant_id}",
                    namespace=self.namespace
                )
            except ApiException as e:
                if e.status != 404:
                    logger.error(f"Failed to delete Deployment for tenant {tenant_id}: {e}")
            
            # 从注册表中移除
            self.registry.unregister_container(tenant_id)
            
            # 删除数据库记录
            UserContainer.objects.filter(user_id=tenant_id).delete()
            
            logger.info(f"Deleted all resources for tenant {tenant_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete resources for tenant {tenant_id}: {e}")
            raise

    def _select_instance_by_response_time(self, tenant_id: str) -> Optional[Dict]:
            """基于响应时间选择最优容器实例（借鉴现有健康检查和端点获取逻辑）"""
            # 从数据库获取容器实例的响应时间指标（参考RouteLog模型的response_time字段）
            instances = ContainerInstance.objects.filter(
                container__user_id=tenant_id,
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