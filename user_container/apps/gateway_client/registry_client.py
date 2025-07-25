import requests
import asyncio
from django.conf import settings
from django.utils import timezone
from .models import ServiceInstance
import logging

logger = logging.getLogger(__name__)

class GatewayRegistryClient:
    """与User Gateway进行服务注册/健康上报的客户端"""
    
    def __init__(self):
        self.gateway_base_url = settings.USER_GATEWAY_URL
        self.register_endpoint = f"{self.gateway_base_url}/api/register/"
        self.health_report_endpoint = f"{self.gateway_base_url}/api/health/"

    def register_service(self, user_container_id, service_type, host, port):
        """向网关注册服务实例 - 由user_client发起"""
        payload = {
            "user_container_id": user_container_id,
            "service_type": service_type,
            "host": host,
            "port": port
        }
        
        try:
            response = requests.post(
                self.register_endpoint,
                json=payload,
                timeout=getattr(settings, 'GATEWAY_REQUEST_TIMEOUT', 10)
            )
            response.raise_for_status()
            
            # 保存到本地数据库
            service_id = f"{user_container_id}_{service_type}"
            ServiceInstance.objects.update_or_create(
                service_id=service_id,
                defaults={
                    'service_type': service_type,
                    'host': host,
                    'port': port,
                    'health_status': 'healthy',
                    'registered_at': timezone.now()
                }
            )
            
            logger.info(f"服务{service_id}注册成功")
            return {'status': 'success', 'service_id': service_id}
            
        except Exception as e:
            logger.error(f"服务注册失败: {e}")
            return {'status': 'error', 'error': str(e)}

    def report_health_status(self, service_id, is_healthy, detail=None):
        """向网关上报健康状态 - 由user_client发起"""
        health_status = 'healthy' if is_healthy else 'unhealthy'
        payload = {
            "service_id": service_id,
            "is_healthy": is_healthy,
            "health_status": health_status,
            "detail": detail or {}
        }
        
        try:
            response = requests.post(
                self.health_report_endpoint,
                json=payload,
                timeout=getattr(settings, 'GATEWAY_REQUEST_TIMEOUT', 10)
            )
            response.raise_for_status()
            
            # 更新本地数据库
            ServiceInstance.objects.filter(service_id=service_id).update(
                health_status=health_status,
                last_health_check=timezone.now()
            )
            
            logger.info(f"服务{service_id}健康状态上报成功: {health_status}")
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"健康状态上报失败: {e}")
            return {'status': 'error', 'error': str(e)}

    async def health_check_port_listener(self, host='0.0.0.0', port=8080):
        """端口循环监听器 - Django集成版本"""
        from aiohttp import web
        from .tasks import collect_exceptions_task, report_exceptions_task
        
        async def handle_health_check(request):
            data = await request.json()
            container_id = data.get('container_id')
            status = data.get('status')  # healthy/unhealthy/terminated
            service_type = data.get('service_type')
            
            service_id = f"{container_id}_{service_type}"
            
            try:
                instance = ServiceInstance.objects.get(service_id=service_id)
                old_status = instance.health_status
                instance.health_status = status
                instance.last_health_check = timezone.now()
                instance.save()
                
                # 状态变化时上报
                if old_status != status:
                    self.report_health_status(service_id, status == 'healthy')
                    
                    # 状态变化时触发异常收集
                    if status == 'unhealthy':
                        collect_exceptions_task.delay()
                        
                    # 如果状态变为健康，触发异常上报
                    if status == 'healthy' and old_status == 'unhealthy':
                        report_exceptions_task.delay()
                        
                    # 服务终止时触发最终上报
                    if status == 'terminated':
                        report_exceptions_task.delay()
                
                return web.json_response({
                    'status': 'success',
                    'message': f'状态更新为 {status}'
                })
                
            except ServiceInstance.DoesNotExist:
                return web.json_response({
                    'status': 'error',
                    'message': '服务实例不存在'
                }, status=404)

        async def trigger_exception_collection(request):
            task = collect_exceptions_task.delay()
            return web.json_response({
                'status': 'success',
                'task_id': task.id
            })

        app = web.Application()
        app.router.add_post('/health-status', handle_health_check)
        app.router.add_post('/collect-exceptions', trigger_exception_collection)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"🚀 健康检查监听器启动在 {host}:{port}")
        
        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            await runner.cleanup()

    def start_health_listener_sync(self, host='0.0.0.0', port=8080):
        """同步启动健康监听器"""
        asyncio.run(self.health_check_port_listener(host, port))