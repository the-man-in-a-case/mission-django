import requests
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import ServiceInstance
from .registry_client import GatewayRegistryClient
from common.utils import get_current_user_container_id
from django.conf import settings

@require_http_methods(["POST"])
def register_service(request):
    """向网关注册当前容器服务实例"""
    user_container_id = get_current_user_container_id()  # 从上下文中获取用户容器ID
    service_type = request.POST.get('service_type')
    host = request.META.get('HTTP_HOST').split(':')[0]  # 获取容器服务IP
    port = settings.SERVICE_PORT  # 从配置中获取服务端口
    
    registry_client = GatewayRegistryClient()
    result = registry_client.register(
        user_container_id=user_container_id,
        service_type=service_type,
        host=host,
        port=port
    )
    
    if result.get('status') == 'success':
        # 本地存储注册信息
        ServiceInstance.objects.update_or_create(
            service_id=result['service_id'],
            defaults={
                'service_type': service_type,
                'host': host,
                'port': port
            }
        )
        return JsonResponse({'code': 200, 'msg': '注册成功'})
    return JsonResponse({'code': 500, 'msg': result['error']}, status=500)

@require_http_methods(["GET"])
def report_health(request):
    """向网关上报当前服务健康状态"""
    service_id = request.GET.get('service_id')
    is_healthy = request.GET.get('is_healthy', 'true') == 'true'
    
    instance = ServiceInstance.objects.filter(service_id=service_id).first()
    if not instance:
        return JsonResponse({'code': 404, 'msg': '服务实例不存在'}, status=404)
    
    registry_client = GatewayRegistryClient()
    result = registry_client.report_health(service_id, is_healthy)
    
    if result.get('status') == 'success':
        instance.is_healthy = is_healthy
        instance.save()
        return JsonResponse({'code': 200, 'msg': '健康状态上报成功'})
    return JsonResponse({'code': 500, 'msg': result['error']}, status=500)
from django.shortcuts import render

# Create your views here.
