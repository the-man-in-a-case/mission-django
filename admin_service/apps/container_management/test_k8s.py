# 10942al910dr2.vicp.fun:12026
import os
import sys
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from kubernetes import client
from kubernetes.config.kube_config import KubeConfigLoader
from kubernetes.client import Configuration
import base64
import urllib3 

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_k8s_connection():
    """测试Kubernetes集群连接并执行基本检查"""
    try:
        # 尝试从默认位置加载kubeconfig或使用in-cluster配置
        # try:
        #     config.load_kube_config()
        #     print("✅ 已从本地kubeconfig文件加载配置")
        # except config.ConfigException:
        #     try:
        #         config.load_incluster_config()
        #         print("✅ 已从集群内环境加载配置")
        #     except config.ConfigException as e:
        #         print(f"❌ 无法加载Kubernetes配置: {e}")
        #         print("请确保已正确配置kubeconfig或在集群内运行")
        #         return False
        from kubernetes.client import Configuration

        # 手动定义配置参数
        kube_config_dict = {
    "apiVersion": "v1",
    "clusters": [
        {
            "cluster": {
                "server": "https://10942al910dr2.vicp.fun:12026",
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
                "client-certificate-data": "LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1JSURJVENDQWdtZ0F3SUJBZ0lJYi9ya3VCdTB1WkF3RFFZSktvWklodmNOQVFFTEJRQXdGVEVUTUJFR0ExVUUKQXhNS2EzVmlaWEp1WlhSbGN6QWVGdzB5TlRBek1qVXdORE14TURGYUZ3MHlOakF6TWpVd05ETTJNREphTURReApGekFWQmdOVkJBb1REbk41YzNSbGJUcHRZWE4wWlhKek1Sa3dGd1lEVlFRREV4QnJkV0psY201bGRHVnpMV0ZrCmJXbHVNSUlCSWpBTkJna3Foa2lHOXcwQkFRRUZBQU9DQVE4QU1JSUJDZ0tDQVFFQXFUcFBqSVdjVGxTdlByTTgKci9QWEovSjJRSVpDcWh2YXZpaDd4RzhoSVpBcy9waFBjYVBJZDEyOFc0SkZuWmU3TTd4K29CL1B3V1hNN0kzWQpOdDJDa09oUzB0aGZYamdCaFh5V2g1Qm92NWRmeWg3TlZyRVU4V1phaXFMMTFmcVhBK2FSZDU4OENzSVYvYWhPCnR4cElTeXBqN29pTVhZT09yYkFHVnlFY0ovOEtZalpnVEFpbXBoRjAvMFJ6SmkyTVU0SXFDRlhWY0JUaTA3dlMKcWF6VGNyNENLdXp5Y1hQMGJxN0d5UXQyS3dsMmE0R2ZsYWpFNVpHS1JsOGVNdVVpRTAzeGRqQmg2SXR4bys5dApiSU56eitMakpZSkNBZlBSbEd6cUtnQ1JZRWVSWGFnbXp5L3p0Y0RtVnkwSEQ1TXVZZzNlOTdTZzJ6dmRCWGZwClIyaTdWd0lEQVFBQm8xWXdWREFPQmdOVkhROEJBZjhFQkFNQ0JhQXdFd1lEVlIwbEJBd3dDZ1lJS3dZQkJRVUgKQXdJd0RBWURWUjBUQVFIL0JBSXdBREFmQmdOVkhTTUVHREFXZ0JUTk5wakVKaVExZnVOSlBZcjdtQWltc2dsNwpyREFOQmdrcWhraUc5dzBCQVFzRkFBT0NBUUVBQ1EvWGtSTkFZNXF5MmwzTE91K1EzZW5oeUJiS1ZyTGpRZ210ClIwOGp1blNpYTJYTVoxcC9JaCtaM2o1N0c2U3haaTE3ZjlFbzYvMlVQcG5WZGJJTTRvVkZMRUNKb1BwcElyMjMKREF5V0krdDJ6ZlBsM0docEtWMzlzOGZSSVBsZUVIMTFYV2xqTGREU3BoaHFYbFJUQ01CV2hpVXQwRDc3OUpjOApUM2lZMVFiMDl2dDlVNytaS3ZNWERHL2JYL3d1bFhKQnZZbW9PeXVJNGkzYzkreG4wZ1JTL2laS01lZlhuMmtuCjR3dStpcFVWTzF3RmN0SmJnRzk5TEg4T21WcDMyVEltTy9WQzkzRVd1aWdpdXVjVWhaUHNCMnQwNTFLbTNXRncKSUxNM0pXZG5vaTVSSUE3VFNjb2FUa1hLY3R2alVSallHR2RMZDZkclhQMFBCcklHZ0E9PQotLS0tLUVORCBDRVJUSUZJQ0FURS0tLS0tCg==",  # 省略
                "client-key-data": "LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlFb3dJQkFBS0NBUUVBcVRwUGpJV2NUbFN2UHJNOHIvUFhKL0oyUUlaQ3FodmF2aWg3eEc4aElaQXMvcGhQCmNhUElkMTI4VzRKRm5aZTdNN3grb0IvUHdXWE03STNZTnQyQ2tPaFMwdGhmWGpnQmhYeVdoNUJvdjVkZnloN04KVnJFVThXWmFpcUwxMWZxWEErYVJkNTg4Q3NJVi9haE90eHBJU3lwajdvaU1YWU9PcmJBR1Z5RWNKLzhLWWpaZwpUQWltcGhGMC8wUnpKaTJNVTRJcUNGWFZjQlRpMDd2U3FhelRjcjRDS3V6eWNYUDBicTdHeVF0Mkt3bDJhNEdmCmxhakU1WkdLUmw4ZU11VWlFMDN4ZGpCaDZJdHhvKzl0YklOenorTGpKWUpDQWZQUmxHenFLZ0NSWUVlUlhhZ20KenkvenRjRG1WeTBIRDVNdVlnM2U5N1NnMnp2ZEJYZnBSMmk3VndJREFRQUJBb0lCQUdTWFVLbkswZnFOeEEyVgpKVUhCdytidTdQTzEydkthMUErc3FNVSsrWWFsMk5rTldFdkllMlRZeHhudCtjdVBZYXVESkJHeVZ5QXlqdmtkCjU2UFZUOE1yRmZCV3hYbVArUGVMOHo1cHpKbjJOTzVFR1BLckdEUFdENFBSRWlnN2FJRGRFU0wxK0E2OUI2MWIKMms1a3hReEpDbFhEdlF2cEkycUM4NEhmSUlsMHpRRGcvK2NFV2RwMW1Nbjhzd2Z1aWJZdTU1YXlKRTliY085egpseStSS3RiRndRdHlLS1k4RG1QQzBMTjVoSW5FWVExRm1ENFl6U0g1TTVQb1J4TFFQKytUcnRpSlFLY3VpVDg5CnAzQi9tc1ZSYnFKdHZqdHByRjYveHF1UFBrVzFhYVV4a2s2c2dYWGp1Z1hjRk96MDlOL1FRZEphTzFGaXdiS1cKOFRRRzFlRUNnWUVBMWZ1QWtaV0tpVDY4ejNrUURsek5XOFk1eWVEbTFvSTFaZlhNVE0ycmZSK20xSndPa3ZNbQpWaVpPVW1pQjlzT0g1cDRCcFZDWHN0VHR0bStPL21qZUM3SzAzWHdxOUp2SHM0Q0FxT1BreTViekJwS0ZlWlJsCnh5Q3RuNHl4Z3ArMUNNSzB3ZDdhVGxBcEVXdSswOEVJdThlZVg5c1lTcWdQRWl3SFNDMy9vMHNDZ1lFQXluVVQKVkFKbnRxSUg4dU1KaW15VFc1cU5tZmtOdDdYYjZUTDN0UEY2aHNVckRTcHZVRkxmdlFuakNtM2dOeDlSaTNzZwoxcUMrNFF5dWhBYi9EUzlDZ0l4QythbXd1YlhxQ2VqU2JVYXNucXlzVlVFaFVQTS9GRE9VL09RVnFjRkNCZzB4CjlWcFQ2UXFiOVk1NEY0cTVPWTYwV3ZPR2RLci80Q0hhbHZ4ajlLVUNnWUJqOWJ3bXhqdlVSMGwraGloWS9VTTEKaHhGQjNGMFpnZlFkOEVnQzdPVWFhMm5NMGlZQXdiTjc5U01MWGlTd09NRkltekZibjUxdC9nZ1ovRjFKUFlYVQo0eU9ZZjhPMVJ2eHdQeXhiT1RLTlpMT2NzMS9FM3V6NHE2eFA1ektaT2JBaEtvdTBNVDI3N2JoeG1lcW9Fdm5ZCmRyVG1SSHhCaSthV2I1anJRQW0ycHdLQmdRQ0hKeHplQ2pUK1FMQ1p2bUtTRytWTFU2T1AxQ2tLS01kRHFCaWcKbkV1MVNFNXpIWTd0eWtVK1J5bGZ2dlhkRm5VemJlRUFKcE1HWFpicTRGakhqbk1RcVpIVVpTbHE4RHZxblpoTQpCdEFacFIvdVVlcFJ4ZkNvSmI4aUM0bENwNWJSdjJGSWJ5SnhBZm9YTlNLS1pMczk1endUTTFyZzYzNmhPemhYCmJ1bXpXUUtCZ0NlQTg4eDdMYUNWZlQ5WEZrMkVjbFZXbFBLek9kNWVKS09JR0NucEVHVGg1WkVMODBxbDF1Wk4KSHh2NmNKUFFwZm5DaWo2ZkROVkJXazR2RWJIaWE0Wlg5YlZmSE9kTlcvcFp5d1BZWmtqZXpFWUxVRnVQS3Z5SQpoMmxzU1o1YkRuSjJLMUlwaVlnaHErdFVwbE1sNE5nUnJSaHRYWmMrK2xVemZ4cFpTWllxCi0tLS0tRU5EIFJTQSBQUklWQVRFIEtFWS0tLS0tCg=="  # 省略
            }
        }
    ]
}

        # 加载配置
# 使用 KubeConfigLoader 从 dict 加载配置
        loader = KubeConfigLoader(config_dict=kube_config_dict)
        configuration = Configuration()
        loader.load_and_set(configuration)

        # 设置为默认配置
        client.Configuration.set_default(configuration)

        # 创建API客户端实例
        v1 = client.CoreV1Api()
        print("✅ API客户端创建成功")
        apps_v1 = client.AppsV1Api() 
        # 测试API服务器连接
        try:
            version = client.VersionApi().get_code()
            print(f"✅ 成功连接到Kubernetes API服务器 - 版本: {version.git_version}")
        except ApiException as e:
            print(f"❌ API请求失败: {e}")
            return False

        # 列出命名空间以验证权限
        try:
            namespaces = v1.list_namespace().items
            print(f"✅ 成功获取命名空间列表 (找到 {len(namespaces)} 个命名空间)")
            for ns in namespaces[:3]:  # 显示前3个命名空间
                print(f"  - {ns.metadata.name}")
            if len(namespaces) > 3:
                print(f"  - ... 等 {len(namespaces)} 个命名空间")
        except ApiException as e:
            print(f"⚠️ 获取命名空间失败: {e}")
            print("  这可能是权限问题（当前用户可能没有list namespaces权限）")

        # 检查节点状态
        try:
            nodes = v1.list_node().items
            if not nodes:
                print("⚠️ 未发现可用节点")
            else:
                print(f"✅ 成功获取节点列表 (找到 {len(nodes)} 个节点)")
                for node in nodes:
                    node_name = node.metadata.name
                    # 获取节点状态条件
                    conditions = {c.type: c.status for c in node.status.conditions}
                    ready_status = conditions.get("Ready", "Unknown")
                    print(f"  - {node_name} ({ready_status})")
        except ApiException as e:
            print(f"⚠️ 获取节点信息失败: {e}")

        try:
            deployments = apps_v1.list_deployment_for_all_namespaces().items
            print(f"✅ AppsV1Api测试成功：找到 {len(deployments)} 个Deployment")
            for dep in deployments[:3]:
                print(f"  - {dep.metadata.namespace}/{dep.metadata.name}")
        except ApiException as e:
            print(f"⚠️ AppsV1Api测试失败（Deployment）: {e}")


        return True

    except Exception as e:
        print(f"❌ 发生未知错误: {e}")
        return False

if __name__ == "__main__":
    print("开始Kubernetes连接测试...")
    result = test_k8s_connection()
    if result:
        print("\n✅ 所有测试完成，Kubernetes连接正常")
    else:
        print("\n❌ 测试失败，Kubernetes连接存在问题")
        sys.exit(1)    