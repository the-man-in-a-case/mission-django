from kubernetes import client, config
from django.conf import settings
from kubernetes.config.kube_config import KubeConfigLoader
from kubernetes.client import Configuration
import urllib3 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class K8sClient:
    def __init__(self):
        # 手动定义Kubernetes配置参数
        kube_config_dict = {
    "apiVersion": "v1",
    "clusters": [
        {
            "cluster": {
                "server": "https://33tnzu502552.vicp.fun:49147",
                "certificate-authority-data": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURCVENDQWUyZ0F3SUJBZ0lJVE15QnBxNFBING93RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TlRBek1qVXdORE14TURGYUZ3MHpOVEF6TWpNd05ETTJNREZhTUJVeApFekFSQmdOVkJBTVRDbXQxWW1WeWJtVjBaWE13Z2dFaU1BMEdDU3FHU0liM0RRRUJBUVVBQTRJQkR3QXdnZ0VLCkFvSUJBUUM1V0hYa3VESFN4cDViNUVsRlhGbElEWktlL29PNzNUTzhWTktuWXZHTmYvRDlZZXlzYUF4eDZSTDYKWmtOM0psWWNiVzh3N2pWZlAvN1g4d3k0UjZwVTZ3Umc1cVc2OXZDYUJ4QTI1Ynd2RWpYS2N1UHhBS0JqMnc5Uwo5a0N2eG1wT0lNR215RDBnYjJVR3ArK1FVTWRaOUd6VkNRSm9xQWdlNUQ1TFV0YWNVWXY5SzJpdHQzcE9zQU9SCkEvUXpJcDJrbUFqUE85RHhTT2g4ZEVFdUtJQmNaWDB5UXBKZ1M3TnY1S2ZpTGVDRnhKeTdUNCtYcWxzRjVlb2oKV1kyU2gyRC9ZOHFIM2hwa0FmVUdJa3EvbGR6UnE4QWJRSTBTeUl1bEpyc1ZaanV2Mld2SzRVdVYybW56U3kyVwp3aE1tVzBMYms3RXFxLzZRc25mYkJtTkoyWms1QWdNQkFBR2pXVEJYTUE0R0ExVWREd0VCL3dRRUF3SUNwREFQCkJnTlZIUk1CQWY4RUJUQURBUUgvTUIwR0ExVWREZ1FXQkJUTk5wakVKaVExZnVOSlBZcjdtQWltc2dsN3JEQVYKQmdOVkhSRUVEakFNZ2dwcmRXSmxjbTVsZEdWek1BMEdDU3FHU0liM0RRRUJDd1VBQTRJQkFRQktqMytnYytFKwp2VjBOTllFTDVJQjR0dUxha00vY012YkpPVjd4T3d5ckhoVHYxR0o3TTBHd0hJTjdRbllzeFBENWR2M1FlS0ZwCnlvNittVEsrMVRveVRCdXR2YkdWMzRxVHQ4Um14eXVkeXZ6UjNrbUNYQjN3VkZHSUhkSE9JRjh3QitwdllLV3YKNUZ5Q2dBSUVrendkUzhueU0vUWhYNDhKbkVSWFlWL0JnR3pxeFVxNTE3RmRLditCOHdQekZ1ZFBGN0tNUVB5agpFOCtXRS9SeFE4UkJIOHZ1a2VJSTMyZ3NXOGZLZ3Y5MXQzbGhFRlpiYXFOQys2Mm1nYk5hSnZycTdOS1MrdGZRCkdmYy9JbEw0SEVURFFYRkhsUktsaGp5dUM3N0Y4cmFJTExidWVpVlVtUzNuSUZ1QW9lWWhNUkhseUQ4K0NnYkoKRzYybnpRWUNQTHlpCi0tLS0tRU5EIENFUlRJRklDQVRFLS0tLS0K" , 
                "insecure-skip-tls-verify": True 
            },
            "name": "kubernetes"
        }
    ],
    "contexts": [
        {
            "context": {
                "cluster": "kubernetes",
                "user": "kubernetes-admin"
            },
            "name": "kubernetes-admin@kubernetes"
        }
    ],
    "current-context": "kubernetes-admin@kubernetes",
    "kind": "Config",
    "preferences": {},
    "users": [
        {
            "name": "kubernetes-admin",
            "user": {
                "client-certificate-data": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURJVENDQWdtZ0F3SUJBZ0lJYi9ya3VCdTB1WkF3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TlRBek1qVXdORE14TURGYUZ3MHlOakF6TWpVd05ETTJNREphTURReApGekFWQmdOVkJBb1REbk41YzNSbGJUcHRZWE4wWlhKek1Sa3dGd1lEVlFRREV4QnJkV0psY201bGRHVnpMV0ZrCmJXbHVNSUlCSWpBTkJna3Foa2lHOXcwQkFRRUZBQU9DQVE4QU1JSUJDZ0tDQVFFQXFUcFBqSVdjVGxTdlByTTgKci9QWEovSjJRSVpDcWh2YXZpaDd4RzhoSVpBcy9waFBjYVBJZDEyOFc0SkZuWmU3TTd4K29CL1B3V1hNN0kzWQpOdDJDa09oUzB0aGZYamdCaFh5V2g1Qm92NWRmeWg3TlZyRVU4V1phaXFMMTFmcVhBK2FSZDU4OENzSVYvYWhPCnR4cElTeXBqN29pTVhZT09yYkFHVnlFY0ovOEtZalpnVEFpbXBoRjAvMFJ6SmkyTVU0SXFDRlhWY0JUaTA3dlMKcWF6VGNyNENLdXp5Y1hQMGJxN0d5UXQyS3dsMmE0R2ZsYWpFNVpHS1JsOGVNdVVpRTAzeGRqQmg2SXR4bys5dApiSU56eitMakpZSkNBZlBSbEd6cUtnQ1JZRWVSWGFnbXp5L3p0Y0RtVnkwSEQ1TXVZZzNlOTdTZzJ6dmRCWGZwClIyaTdWd0lEQVFBQm8xWXdWREFPQmdOVkhROEJBZjhFQkFNQ0JhQXdFd1lEVlIwbEJBd3dDZ1lJS3dZQkJRVUgKQXdJd0RBWURWUjBUQVFIL0JBSXdBREFmQmdOVkhTTUVHREFXZ0JUTk5wakVKaVExZnVOSlBZcjdtQWltc2dsNwpyREFOQmdrcWhraUc5dzBCQVFzRkFBT0NBUUVBQ1EvWGtSTkFZNXF5MmwzTE91K1EzZW5oeUJiS1ZyTGpRZ210ClIwOGp1blNpYTJYTVoxcC9JaCtaM2o1N0c2U3haaTE3ZjlFbzYvMlVQcG5WZGJJTTRvVkZMRUNKb1BwcElyMjMKREF5V0krdDJ6ZlBsM0docEtWMzlzOGZSSVBsZUVIMTFYV2xqTGREU3BoaHFYbFJUQ01CV2hpVXQwRDc3OUpjOApUM2lZMVFiMDl2dDlVNytaS3ZNWERHL2JYL3d1bFhKQnZZbW9PeXVJNGkzYzkreG4wZ1JTL2laS01lZlhuMmtuCjR3dStpcFVWTzF3RmN0SmJnRzk5TEg4T21WcDMyVEltTy9WQzkzRVd1aWdpdXVjVWhaUHNCMnQwNTFLbTNXRncKSUxNM0pXZG5vaTVSSUE3VFNjb2FUa1hLY3R2alVSallHR2RMZDZkclhQMFBCcklHZ0E9PQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg=="  
            }
        }
    ]
}

        # 加载配置
        loader = KubeConfigLoader(config_dict=kube_config_dict)
        configuration = Configuration()
        loader.load_and_set(configuration)

        # 设置为默认配置
        client.Configuration.set_default(configuration)

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