from .k8s_client import K8sClient

class ContainerOrchestrator:
    def __init__(self):
        self.k8s_client = K8sClient()

    def create_k8s_resources(self, user_id: str, tenant_id: str) -> tuple:
        """创建K8s Deployment和Service（结构与yaml模板一致）"""
        deployment_name = f"user-container-dep-{tenant_id}"
        service_name = f"user-container-svc-{tenant_id}"

        deployment_spec = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": deployment_name
            },
            "spec": {
                "replicas": 1,
                "selector": {
                    "matchLabels": {
                        "app": "user-container",
                        "tenant": tenant_id
                    }
                },
                "template": {
                    "metadata": {
                        "labels": {
                            "app": "user-container",
                            "tenant": tenant_id
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "name": "user-container",
                                "image": "user_container:latest",
                                "imagePullPolicy": "IfNotPresent",
                                "ports": [
                                    {"containerPort": 8000, "name": "http"}
                                ],
                                "env": [
                                    {"name": "USER_ID", "value": str(user_id)},
                                    {"name": "TENANT_ID", "value": str(tenant_id)},
                                    {"name": "ADMIN_SERVICE_URL", "value": "http://admin-service:80"},
                                    {"name": "GATEWAY_URL", "value": "http://user-gateway:80"}
                                ],
                                "startupProbe": {
                                    "httpGet": {"path": "/healthz", "port": "http"},
                                    "failureThreshold": 30,
                                    "periodSeconds": 10
                                },
                                "livenessProbe": {
                                    "httpGet": {"path": "/healthz", "port": "http"},
                                    "initialDelaySeconds": 20,
                                    "periodSeconds": 30
                                },
                                "readinessProbe": {
                                    "httpGet": {"path": "/readyz", "port": "http"},
                                    "initialDelaySeconds": 10,
                                    "periodSeconds": 10
                                },
                                "resources": {
                                    "requests": {"cpu": "100m", "memory": "128Mi"},
                                    "limits": {"cpu": "250m", "memory": "256Mi"}
                                }
                            }
                        ]
                    }
                }
            }
        }

        service_spec = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": service_name
            },
            "spec": {
                "selector": {
                    "app": "user-container",
                    "tenant": tenant_id
                },
                "ports": [
                    {"protocol": "TCP", "port": 80, "targetPort": 8000}
                ]
            }
        }

        self.k8s_client.create_deployment(deployment_name, deployment_spec)
        self.k8s_client.create_service(service_name, service_spec)
        return deployment_name, service_name

    def delete_k8s_resources(self, deployment_name: str, service_name: str) -> None:
        """删除K8s Deployment和Service"""
        self.k8s_client.delete_deployment(deployment_name)
        self.k8s_client.delete_service(service_name)

    def start_deployment(self, deployment_name: str) -> None:
        """启动Deployment（恢复副本数）"""
        self.k8s_client.scale_deployment(deployment_name, replicas=1)

    def stop_deployment(self, deployment_name: str) -> None:
        """停止Deployment（设置副本数为0）"""
        self.k8s_client.scale_deployment(deployment_name, replicas=0)

    def restart_deployment(self, deployment_name: str) -> None:
        """重启Deployment（滚动更新）"""
        self.k8s_client.rollout_restart_deployment(deployment_name)

    def update_deployment_resources(self, deployment_name: str, resource_config: dict) -> None:
        """更新Deployment资源限制"""
        self.k8s_client.patch_deployment(
            deployment_name,
            {"spec": {"template": {"spec": {"containers": [{
                "resources": {"limits": {
                    "cpu": resource_config["cpu_limit"],
                    "memory": resource_config["memory_limit"]
                }}
            }]}}}}
        )