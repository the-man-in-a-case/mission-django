import redis
import requests
from influxdb import InfluxDBClient
from django.conf import settings
from django.utils import timezone
from .models import ExceptionData, MetricsData
import logging
import json

logger = logging.getLogger(__name__)

class ExceptionCollectorService:
    """异常数据收集服务"""
    
    def __init__(self):
        self.redis_client = redis.Redis(
            host=getattr(settings, 'REDIS_HOST', 'localhost'),
            port=getattr(settings, 'REDIS_PORT', 6379),
            db=getattr(settings, 'REDIS_DB', 0),
            decode_responses=True
        )
        
        self.influx_client = InfluxDBClient(
            host=getattr(settings, 'INFLUXDB_HOST', 'localhost'),
            port=getattr(settings, 'INFLUXDB_PORT', 8086),
            username=getattr(settings, 'INFLUXDB_USERNAME', 'admin'),
            password=getattr(settings, 'INFLUXDB_PASSWORD', 'admin'),
            database=getattr(settings, 'INFLUXDB_DATABASE', 'monitoring')
        )

    def collect_exceptions_from_redis(self):
        """从Redis收集异常数据"""
        try:
            exceptions = self.redis_client.lrange('gateway_client_exceptions', 0, -1)
            collected_count = 0
            
            for exception_data in exceptions:
                data = json.loads(exception_data)
                # 新增：写入共享userdb
                from shared_models.userdb.models import BusinessErrorLog
                BusinessErrorLog.objects.create(
                    container_instance_id=data.get('container_id'),
                    error_type=data.get('exception_type'),
                    error_message=data.get('exception_message'),
                    stack_trace=data.get('stack_trace', ''),
                    occurred_at=data.get('timestamp', timezone.now())
                )
                ExceptionData.objects.create(
                    container_id=data.get('container_id'),
                    service_name=data.get('service_name'),
                    source='redis',
                    exception_type=data.get('exception_type'),
                    exception_message=data.get('exception_message'),
                    stack_trace=data.get('stack_trace', ''),
                    severity=data.get('severity', 'medium')
                )
                collected_count += 1
            
            self.redis_client.delete('gateway_client_exceptions')
            logger.info(f"从Redis收集 {collected_count} 条异常数据")
            return collected_count
            
        except Exception as e:
            logger.error(f"Redis异常收集失败: {e}")
            return 0

    def collect_exceptions_from_influxdb(self):
        """从InfluxDB收集异常数据"""
        try:
            query = """
                SELECT * FROM exceptions 
                WHERE time >= now() - 1h 
                AND source = 'gateway_client'
                AND reported = false
            """
            
            result = self.influx_client.query(query)
            collected_count = 0
            
            for point in result.get_points():
                ExceptionData.objects.create(
                    container_id=point.get('container_id'),
                    service_name=point.get('service_name'),
                    source='influxdb',
                    exception_type=point.get('exception_type'),
                    exception_message=point.get('message'),
                    stack_trace=point.get('stack_trace', ''),
                    severity=point.get('severity', 'medium')
                )
                collected_count += 1
            
            logger.info(f"从InfluxDB收集 {collected_count} 条异常数据")
            return collected_count
            
        except Exception as e:
            logger.error(f"InfluxDB异常收集失败: {e}")
            return 0

    def collect_all_exceptions(self):
        """收集所有来源的异常数据"""
        redis_count = self.collect_exceptions_from_redis()
        influx_count = self.collect_exceptions_from_influxdb()
        total = redis_count + influx_count
        logger.info(f"总共收集 {total} 条异常数据")
        return total

    def report_unreported_exceptions(self):
        """上报未上报的异常数据"""
        unreported = ExceptionData.objects.filter(is_reported=False)
        
        if not unreported.exists():
            return 0

        report_data = []
        for exception in unreported:
            report_data.append({
                'container_id': exception.container_id,
                'service_name': exception.service_name,
                'exception_type': exception.exception_type,
                'exception_message': exception.exception_message,
                'severity': exception.severity,
                'timestamp': exception.timestamp.isoformat(),
                'source': exception.source
            })

        try:
            response = requests.post(
                f"{settings.ROUTE_MANAGEMENT_URL}/api/exceptions/report/",
                json={'exceptions': report_data},
                timeout=10
            )
            
            if response.status_code == 200:
                count = unreported.update(is_reported=True)
                logger.info(f"上报 {count} 条异常数据成功")
                return count
            else:
                logger.error(f"异常上报失败: {response.status_code}")
                return 0
                
        except Exception as e:
            logger.error(f"异常上报错误: {e}")
            return 0

    def report_metrics(self, service_id, metrics):
        """上报指标数据"""
        try:
            # 保存到本地数据库
            for metric_name, metric_value in metrics.items():
                if isinstance(metric_value, (int, float)):
                    MetricsData.objects.create(
                        service_id=service_id,
                        metric_name=metric_name,
                        metric_value=float(metric_value),
                        labels=metrics.get('labels', {})
                    )

            # 上报到监控系统
            response = requests.post(
                f"{settings.MONITORING_SERVICE_URL}/api/metrics/",
                json={'service_id': service_id, 'metrics': metrics},
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"指标上报失败: {e}")
            return False