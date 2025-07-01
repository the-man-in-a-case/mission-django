from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import RouteRegistry, RouteLog
from ..userdb.models import ContainerInstance
from .balancer import LoadBalancer
from .circuit_breaker import CircuitBreaker
from django.db.models import F  # 添加F表达式导入

@require_http_methods(["GET"])
def get_healthy_instances(request, tenant_id):
    try:
        route_registry = RouteRegistry.objects.get(user__tenant_id=tenant_id, is_active=True)
        lb = LoadBalancer(route_registry)
        instance = lb.select_instance()
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 实际请求处理逻辑...
        response_status = 200
        response_time = (time.time() - start_time) * 1000
        response_size = 1024
        
        # 创建路由日志
        RouteLog.objects.create(
            route_registry=route_registry,
            container_instance=instance,
            request_id=str(uuid.uuid4()),
            request_method=request.method,
            request_path=request.path,
            request_headers=dict(request.headers),
            client_ip=request.META.get('REMOTE_ADDR', ''),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            target_url=f"http://{instance.pod_ip}:{instance.port}{request.path}",
            load_balance_strategy=lb.strategy,
            response_status=response_status,
            response_time=response_time,
            response_size=response_size
        )
        
        # 更新熔断器成功状态
        cb = CircuitBreaker(instance, lb.config)
        cb.record_success()
        
        return JsonResponse({
            'status': 'success',
            'instance': instance.instance_id,
            'pod_ip': instance.pod_ip,
            'port': instance.port
        })
        
    except Exception as e:
        # 错误处理和日志记录
        if 'route_registry' in locals():
            RouteLog.objects.create(
                route_registry=route_registry,
                container_instance=locals().get('instance'),
                request_id=str(uuid.uuid4()),
                request_method=request.method if 'request' in locals() else '',
                request_path=request.path if 'request' in locals() else '',
                client_ip=request.META.get('REMOTE_ADDR', '') if 'request' in locals() else '',
                user_agent=request.META.get('HTTP_USER_AGENT', '') if 'request' in locals() else '',
                target_url=f"http://{instance.pod_ip}:{instance.port}{request.path}" if 'instance' in locals() else None,
                load_balance_strategy=lb.strategy if 'lb' in locals() else '',
                error_type='server',
                error_message=str(e)
            )
            
            if 'instance' in locals():
                cb = CircuitBreaker(instance, lb.config)
                cb.record_failure()
        
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# Create your views here.
