import requests
import time
import asyncio
import aiohttp
from django.conf import settings
from requests.exceptions import RequestException
from .models import ServiceInstance, HealthCheckResult, ExceptionReport
import logging

logger = logging.getLogger(__name__)

class GatewayRegistryClient:
    """与User Gateway进行服务注册/健康上报的客户端"""
    
    def __init__(self):
        self.gateway_base_url = settings.USER_GATEWAY_URL
        self.register_endpoint = f"{self.gateway_base_url}/api/register/"
        self.health_report_endpoint = f"{self.gateway_base_url}/api/health/"
        self.container_id = None
        self.token = None
    
    def _make_request(self, method, url, data=None):
        """通用请求方法（含异常处理）"""
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                timeout=settings.GATEWAY_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return {'status': 'success', 'data': response.json()}
        except RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response:
                error_msg += f" | 响应内容: {e.response.text}"
            return {'status': 'error', 'error': error_msg}
    
    def register(self, user_container_id, service_type, host, port):
        """向网关注册服务实例"""
        payload = {
            "user_container_id": user_container_id,
            "service_type": service_type,
            "host": host,
            "port": port
        }
        
        result = self._make_request('post', self.register_endpoint, payload)
        
        if result['status'] == 'success':
            # 保存到本地数据库
            service_id = f"{user_container_id}_{service_type}"
            ServiceInstance.objects.update_or_create(
                service_id=service_id,
                defaults={
                    'service_type': service_type,
                    'host': host,
                    'port': port,
                    'health_status': 'healthy'
                }
            )
        
        return result
    
    def report_health(self, service_id, is_healthy):
        """向网关上报健康状态"""
        health_status = 'healthy' if is_healthy else 'unhealthy'
        payload = {
            "service_id": service_id,
            "is_healthy": is_healthy,
            "health_status": health_status
        }
        
        result = self._make_request('post', self.health_report_endpoint, payload)
        
        if result['status'] == 'success':
            # 更新本地数据库
            try:
                instance = ServiceInstance.objects.get(service_id=service_id)
                instance.health_status = health_status
                instance.last_health_check = time.time()
                instance.save()
            except ServiceInstance.DoesNotExist:
                logger.warning(f"服务实例不存在: {service_id}")
        
        return result
    
    def report_metrics(self, metrics):
        """上报客户端指标到监控系统"""
        try:
            response = requests.post(
                f"{settings.ADMIN_SERVICE_URL}/api/monitoring/metrics/",
                json={
                    'container_id': self.container_id,
                    'metrics': metrics,
                    'timestamp': time.time()
                },
                headers={'Authorization': f'Bearer {self.token}'},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"上报指标失败: {str(e)}")
            return False
    
    async def health_check_port_listener(self, host='0.0.0.0', port=8080):
        """端口循环监听 - 监听各容器运行状态"""
        from aiohttp import web
        
        async def handle_health_check(request):
            """处理健康检查请求"""
            data = await request.json()
            container_id = data.get('container_id')
            status = data.get('status')  # healthy, unhealthy, terminated
            service_type = data.get('service_type')
            
            # 更新服务状态
            service_id = f"{container_id}_{service_type}"
            try:
                instance = ServiceInstance.objects.get(service_id=service_id)
                instance.health_status = status
                instance.last_health_check = timezone.now()
                instance.save()
                
                # 记录健康检查结果
                HealthCheckResult.objects.create(
                    service_instance=instance,
                    is_healthy=status == 'healthy',
                    status_code=200 if status == 'healthy' else 500,
                    detail=data
                )
                
                # 向网关上报状态变化
                self.report_health(service_id, status == 'healthy')
                
                return web.json_response({'status': 'success'})
            except ServiceInstance.DoesNotExist:
                return web.json_response({'status': 'error', 'message': '服务实例不存在'})
        
        app = web.Application()
        app.router.add_post('/health-status', handle_health_check)
        
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        logger.info(f"健康检查监听器启动在 {host}:{port}")
        
        try:
            while True:
                await asyncio.sleep(3600)  # 保持运行
        except asyncio.CancelledError:
            await runner.cleanup()
    
    def start_health_listener(self, host='0.0.0.0', port=8080):
        """启动健康检查监听器"""
        asyncio.run(self.health_check_port_listener(host, port))