import requests
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import ServiceInstance
from .registry_client import GatewayRegistryClient
from common.utils import get_current_user_container_id
from django.conf import settings
import json
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from shared_models.userdb.models import BusinessErrorLog, ContainerInstance, ContainerMetric
from .services import GatewayClientService  

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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@csrf_exempt
def report_business_error(request):
    """上报业务异常信息"""
    try:
        data = json.loads(request.body)
        instance_id = data.get('instance_id')
        error_type = data.get('error_type')
        error_message = data.get('error_message')
        stack_trace = data.get('stack_trace', '')

        if not all([instance_id, error_type, error_message]):
            return JsonResponse({
                'code': 400,
                'msg': '缺少必要参数',
                'detail': 'instance_id, error_type和error_message为必填项'
            }, status=400)

        # 获取容器实例
        instance = ContainerInstance.objects.filter(instance_id=instance_id).first()
        if not instance:
            return JsonResponse({
                'code': 404,
                'msg': '容器实例不存在'
            }, status=404)

        # 创建异常日志
        error_log = BusinessErrorLog.objects.create(
            container_instance=instance,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace
        )

        # 新增: 上报到 route_management
        GatewayClientService.report_exception_to_route_management(error_log)

        # 更新容器指标中的异常计数
        metric, created = ContainerMetric.objects.get_or_create(
            container=instance.container,
            timestamp__date=timezone.now().date(),
            defaults={'timestamp': timezone.now()}
        )
        metric.business_error_count += 1
        metric.last_business_error = f'{error_type}: {error_message[:200]}'
        metric.save()

        return JsonResponse({
            'code': 200,
            'msg': '业务异常上报成功',
            'error_id': error_log.id
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'code': 400,
            'msg': '无效的JSON格式'
        }, status=400)
    except Exception as e:
        logger.error(f'业务异常上报失败: {str(e)}')
        return JsonResponse({
            'code': 500,
            'msg': '服务器内部错误',
            'detail': str(e)
        }, status=500)
