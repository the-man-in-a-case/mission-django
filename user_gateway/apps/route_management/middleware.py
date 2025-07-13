import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone  # 添加缺失的导入
from shared_models.userdb.models import RouteMetrics, ContainerInstance

logger = logging.getLogger(__name__)

class RequestMetricsMiddleware(MiddlewareMixin):
    """请求指标采集中间件"""
    def process_request(self, request):
        request.start_time = time.time()
        request.instance_id = request.META.get('HTTP_X_INSTANCE_ID')

    def process_response(self, request, response):
        try:
            if hasattr(request, 'start_time') and request.instance_id:
                # 计算请求耗时
                duration = (time.time() - request.start_time) * 1000  # 毫秒
                instance = ContainerInstance.objects.filter(instance_id=request.instance_id).first()

                if instance:
                    # 更新路由指标
                    metric, created = RouteMetrics.objects.get_or_create(
                        container=instance.container,
                        timestamp__date=timezone.now().date(),
                        defaults={'timestamp': timezone.now()}
                    )
                    metric.total_requests += 1

                    # 记录状态码
                    if 200 <= response.status_code < 300:
                        metric.successful_requests += 1
                    else:
                        metric.failed_requests += 1

                    # 更新延迟统计
                    metric.avg_latency = (
                        (metric.avg_latency * (metric.total_requests - 1) + duration) / metric.total_requests
                    )
                    if duration > metric.max_latency or metric.max_latency == 0:
                        metric.max_latency = duration
                    if duration < metric.min_latency or metric.min_latency == 0:
                        metric.min_latency = duration

                    metric.save()
        except Exception as e:
            logger.error(f'请求指标采集失败: {str(e)}')

        return response

from rest_framework.exceptions import AuthenticationFailed
from .utils import TokenValidator

class TokenAuthenticationMiddleware(MiddlewareMixin):
    """Token认证中间件，对所有请求进行Token验证"""
    
    # 不需要验证的路径列表
    EXEMPT_PATHS = [
        '/api/token/',  # 获取Token的接口本身不需要验证
        '/admin/',      # 管理界面
        '/prometheus/', # 监控指标
    ]
    
    def process_request(self, request):
        # 检查路径是否在豁免列表中
        for path in self.EXEMPT_PATHS:
            if request.path.startswith(path):
                return
                
        # 获取Token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Token '):
            raise AuthenticationFailed('Token header is missing or invalid')
            
        token_key = auth_header.split(' ')[-1]
        if not token_key:
            raise AuthenticationFailed('Token is missing')
            
        # 验证Token
        user = TokenValidator.validate_token(token_key)
        request.user = user