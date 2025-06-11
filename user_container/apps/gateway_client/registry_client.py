import requests
from django.conf import settings
from requests.exceptions import RequestException

class GatewayRegistryClient:
    """与User Gateway进行服务注册/健康上报的客户端"""
    GATEWAY_BASE_URL = settings.USER_GATEWAY_URL  # 从Django配置获取网关地址（如http://user-gateway:8000）
    REGISTER_ENDPOINT = f"{GATEWAY_BASE_URL}/api/register/"
    HEALTH_REPORT_ENDPOINT = f"{GATEWAY_BASE_URL}/api/health/"

    def _make_request(self, method, url, data=None):
        """通用请求方法（含异常处理）"""
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                timeout=settings.GATEWAY_REQUEST_TIMEOUT  # 配置超时时间（如5秒）
            )
            response.raise_for_status()  # 非2xx状态码抛异常
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
        return self._make_request('post', self.REGISTER_ENDPOINT, payload)

    def report_health(self, service_id, is_healthy):
        """向网关上报健康状态"""
        payload = {
            "service_id": service_id,
            "is_healthy": is_healthy
        }
        return self._make_request('post', self.HEALTH_REPORT_ENDPOINT, payload)