import requests
from django.conf import settings

def get_all_maps_from_admin():
    """调用 admin 服务 /resource-management/maps/ 接口获取所有 map 列表"""
    try:
        response = requests.get(
            f"{settings.ADMIN_SERVICE_BASE_URL}/resource-management/maps/",
            timeout=10  # 设置超时时间（秒）
        )
        response.raise_for_status()  # 若状态码非2xx则抛出异常
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"获取 map 列表失败：{str(e)}")

def get_all_layers_from_admin():
    """调用 admin 服务 /resource-management/layers/ 接口获取所有 layer 列表"""
    try:
        response = requests.get(
            f"{settings.ADMIN_SERVICE_BASE_URL}/resource-management/layers/",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"获取 layer 列表失败：{str(e)}")

def get_all_resources_from_admin():
    """合并获取所有 map 和 layer 资源列表"""
    maps = get_all_maps_from_admin()
    layers = get_all_layers_from_admin()
    return {
        "maps": maps,
        "layers": layers
    }

def get_latest_map_from_admin():
    """调用 admin 服务 /resource-management/export/map/latest/ 接口获取最新 map"""
    try:
        response = requests.get(
            f"{settings.ADMIN_SERVICE_BASE_URL}/resource-management/export/map/latest/",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"获取最新 map 失败：{str(e)}")

def get_latest_layer_from_admin():
    """调用 admin 服务 /resource-management/export/layer/latest/ 接口获取最新 layer"""
    try:
        response = requests.get(
            f"{settings.ADMIN_SERVICE_BASE_URL}/resource-management/export/layer/latest/",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"获取最新 layer 失败：{str(e)}")

def get_latest_resources_from_admin():
    """合并获取最新的 map 和 layer 资源"""
    latest_map = get_latest_map_from_admin()
    latest_layer = get_latest_layer_from_admin()
    return {
        "latest_map": latest_map,
        "latest_layer": latest_layer
    }
