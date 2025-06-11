from kubernetes import client, config
from django.conf import settings

class K8sClient:
    def __init__(self):
        # 加载K8s配置（本地开发或集群内）
        if settings.DEBUG:
            config.load_kube_config()
        else:
            config.load_incluster_config()
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()

    def create_deployment(self, name: str, spec: dict) -> None:
        """创建Deployment"""
        deployment = client.V1Deployment(metadata=spec["metadata"], spec=spec["spec"])
        self.apps_v1.create_namespaced_deployment(namespace="user-containers", body=deployment)

    def create_service(self, name: str, spec: dict) -> None:
        """创建Service"""
        service = client.V1Service(metadata=spec["metadata"], spec=spec["spec"])
        self.core_v1.create_namespaced_service(namespace="user-containers", body=service)

    def get_deployment_pods(self, deployment_name: str) -> list:
        """获取Deployment关联的Pod列表"""
        pods = self.core_v1.list_namespaced_pod(
            namespace="user-containers",
            label_selector=f"app={deployment_name}"
        )
        return [{"id": pod.metadata.uid, "name": pod.metadata.name, "ip": pod.status.pod_ip} for pod in pods.items]

    def get_deployment_status(self, deployment_name: str) -> dict:
        """获取Deployment状态"""
        deployment = self.apps_v1.read_namespaced_deployment(
            name=deployment_name,
            namespace="user-containers"
        )
        return {
            "phase": "running" if deployment.status.ready_replicas == deployment.spec.replicas else "pending",
            "ready_replicas": deployment.status.ready_replicas or 0
        }

    def delete_deployment(self, name: str) -> None:
        """删除Deployment"""
        self.apps_v1.delete_namespaced_deployment(
            name=name,
            namespace="user-containers",
            body=client.V1DeleteOptions(propagation_policy="Foreground")
        )

    def delete_service(self, name: str) -> None:
        """删除Service"""
        self.core_v1.delete_namespaced_service(
            name=name,
            namespace="user-containers"
        )

    def scale_deployment(self, name: str, replicas: int) -> None:
        """调整Deployment副本数"""
        deployment = self.apps_v1.read_namespaced_deployment(
            name=name,
            namespace="user-containers"
        )
        deployment.spec.replicas = replicas
        self.apps_v1.replace_namespaced_deployment(
            name=name,
            namespace="user-containers",
            body=deployment
        )