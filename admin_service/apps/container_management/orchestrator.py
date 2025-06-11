from .k8s_client import K8sClient

class ContainerOrchestrator:
    def __init__(self):
        self.k8s_client = K8sClient()

    def create_k8s_resources(self, user_id: str, config: dict) -> tuple:
        """创建K8s Deployment和Service"""
        deployment_name = f"user-{user_id}-deploy"
        service_name = f"user-{user_id}-svc"
        
        # 构造Deployment配置（示例）
        deployment_spec = {
            "metadata": {"name": deployment_name},
            "spec": {
                "replicas": 1,
                "template": {
                    "spec": {
                        "containers": [{
                            "name": "user-container",
                            "image": config.get("image", "business-app:latest"),
                            "resources": {
                                "limits": {
                                    "cpu": config["cpu_limit"],
                                    "memory": config["memory_limit"]
                                }
                            },
                            "env": [{"name": "USER_ID", "value": str(user_id)}]
                        }]
                    }
                }
            }
        }
        
        # 构造Service配置（示例）
        service_spec = {
            "metadata": {"name": service_name},
            "spec": {
                "type": "ClusterIP",
                "ports": [{"port": 8080, "targetPort": 8080}],
                "selector": {"app": deployment_name}
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