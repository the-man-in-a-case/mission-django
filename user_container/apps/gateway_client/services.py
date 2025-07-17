import requests
import logging
from django.conf import settings
from shared_models.userdb.models import BusinessErrorLog

logger = logging.getLogger(__name__)

class GatewayClientService:
    @staticmethod
    def report_exception_to_route_management(error_log: BusinessErrorLog):
        """上报业务异常到 route_management 服务"""
        try:
            payload = {
                'event_type': 'gateway',
                'source': 'gateway_client',
                'level': 'error',
                'message': error_log.error_message,
                'detail': {
                    'error_type': error_log.error_type,
                    'stack_trace': error_log.stack_trace,
                    'instance_id': error_log.container_instance.instance_id,
                    'occurred_at': error_log.occurred_at.isoformat()
                }
            }

            response = requests.post(
                f"{settings.ROUTE_MANAGEMENT_URL}/api/report-status/",
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            logger.info(f"业务异常成功上报到 route_management: {error_log.id}")
            return True
        except Exception as e:
            logger.error(f"上报业务异常到 route_management 失败: {str(e)}")
            return False