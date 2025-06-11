from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import RouteRegistry, RouteLog
from ..userdb.models import ContainerInstance
from .balancer import LoadBalancer

@require_http_methods(["GET"])
def get_healthy_instances(request, user_id):
    """获取用户的健康容器实例"""
    try:
        route = RouteRegistry.objects.get(user__id=user_id, is_active=True)
        instances = ContainerInstance.objects.filter(
            container=route.container,
            is_healthy=True,
            status='running'
        ).order_by('current_connections')  # 按当前连接数排序（最少连接策略）
        lb = LoadBalancer(route)
        selected_instance = lb.select_instance()  # 使用负载均衡策略选择实例
        # 更新实例连接数（需要原子操作避免并发问题）
        ContainerInstance.objects.filter(id=selected_instance.id).update(current_connections=F('current_connections')+1)
        
        return JsonResponse({
            'user_id': user_id,
            'healthy_instances': [
                {
                    'instance_id': inst.instance_id,
                    'pod_ip': inst.pod_ip,
                    'port': inst.port,
                    'current_connections': inst.current_connections
                } for inst in instances
            ]
        })
    except RouteRegistry.DoesNotExist:
        return JsonResponse({'error': 'Route not found'}, status=404)
from django.shortcuts import render

# Create your views here.
