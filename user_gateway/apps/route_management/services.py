import redis
import requests
from influxdb import InfluxDBClient
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
from .models import ContainerHealthRecord, ExceptionData, MetricsData

import psutil
import docker
from kubernetes import client, config

logger = logging.getLogger(__name__)

class RouteManagementService:
    
    @staticmethod
    def report_container_status(container_id, status, resource_data=None):
        """上报容器状态到监控表"""
        ContainerHealthRecord.objects.create(
            container_id=container_id,
            service_name=resource_data.get('service_name', 'unknown'),
            status=status,
            cpu_usage=resource_data.get('cpu_usage'),
            memory_usage=resource_data.get('memory_usage'),
            disk_usage=resource_data.get('disk_usage'),
            network_rx=resource_data.get('network_rx'),
            network_tx=resource_data.get('network_tx'),
            details=resource_data.get('details', '')
        )
        logger.info(f"Container {container_id} status reported: {status}")

    @staticmethod
    def collect_container_resources(container_id):
        """采集容器实际资源使用情况"""
        try:
            # 优先使用Kubernetes API
            config.load_incluster_config()
            v1 = client.CoreV1Api()
            
            # 获取Pod指标
            metrics_client = client.CustomObjectsApi()
            metrics = metrics_client.list_namespaced_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                namespace="user-containers",
                plural="pods"
            )
            
            for pod in metrics['items']:
                if container_id in pod['metadata']['name']:
                    container_metrics = pod['containers'][0]
                    return {
                        'cpu_usage': float(container_metrics['usage']['cpu'].replace('n', '')) / 1000000,
                        'memory_usage': float(container_metrics['usage']['memory'].replace('Ki', '')) / 1024,
                        'disk_usage': psutil.disk_usage('/').percent,
                        'network_rx': float(container_metrics.get('network', {}).get('rx_bytes', 0)),
                        'network_tx': float(container_metrics.get('network', {}).get('tx_bytes', 0))
                    }
                    
        except Exception as e:
            logger.error(f"K8s指标采集失败: {e}")
            # 回退到Docker API
            try:
                docker_client = docker.from_env()
                container = docker_client.containers.get(container_id)
                stats = container.stats(stream=False)
                
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']
                
                return {
                    'cpu_usage': (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0,
                    'memory_usage': (stats['memory_stats']['usage'] / 
                                   stats['memory_stats']['limit']) * 100.0,
                    'disk_usage': psutil.disk_usage('/').percent,
                    'network_rx': stats['networks']['eth0']['rx_bytes'],
                    'network_tx': stats['networks']['eth0']['tx_bytes']
                }
            except Exception as e2:
                logger.error(f"Docker指标采集失败: {e2}")
                return {
                    'cpu_usage': 0, 'memory_usage': 0, 'disk_usage': 0,
                    'network_rx': 0, 'network_tx': 0
                }

class DataCollectorService:
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
            # 假设异常数据存储在Redis的列表中
            exceptions = self.redis_client.lrange('container_exceptions', 0, -1)
            collected_count = 0
            
            for exception_data in exceptions:
                import json
                data = json.loads(exception_data)
                
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
            
            # 清空已处理的异常
            self.redis_client.delete('container_exceptions')
            logger.info(f"Collected {collected_count} exceptions from Redis")
            return collected_count
            
        except Exception as e:
            logger.error(f"Error collecting exceptions from Redis: {e}")
            return 0

    def collect_exceptions_from_influxdb(self):
        """从InfluxDB收集异常数据"""
        try:
            query = """
                SELECT * FROM exceptions 
                WHERE time >= now() - 1h 
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
            
            # 标记已处理的异常
            self.influx_client.write_points([{
                "measurement": "exceptions",
                "tags": {"reported": "true"},
                "fields": {"value": 1}
            }])
            
            logger.info(f"Collected {collected_count} exceptions from InfluxDB")
            return collected_count
            
        except Exception as e:
            logger.error(f"Error collecting exceptions from InfluxDB: {e}")
            return 0

    def collect_all_exceptions(self):
        """收集所有来源的异常数据"""
        redis_count = self.collect_exceptions_from_redis()
        influx_count = self.collect_exceptions_from_influxdb()
        return redis_count + influx_count

    def report_unreported_exceptions(self):
        """上报未上报的异常数据"""
        unreported_exceptions = ExceptionData.objects.filter(is_reported=False)
        
        if not unreported_exceptions.exists():
            return 0

        # 构建上报数据
        report_data = []
        for exception in unreported_exceptions:
            report_data.append({
                'container_id': exception.container_id,
                'service_name': exception.service_name,
                'exception_type': exception.exception_type,
                'exception_message': exception.exception_message,
                'severity': exception.severity,
                'timestamp': exception.timestamp.isoformat()
            })

        # 上报到监控系统
        try:
            response = requests.post(
                f"{settings.MONITORING_SERVICE_URL}/api/exceptions",
                json={'exceptions': report_data},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                unreported_exceptions.update(is_reported=True)
                logger.info(f"Reported {len(report_data)} exceptions")
                return len(report_data)
            else:
                logger.error(f"Failed to report exceptions: {response.status_code}")
                return 0
                
        except Exception as e:
            logger.error(f"Error reporting exceptions: {e}")
            return 0

    def report_metrics(self, service_id, metrics):
        """上报指标数据"""
        try:
            for metric_name, metric_value in metrics.items():
                MetricsData.objects.create(
                    service_id=service_id,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    labels=metrics.get('labels', {})
                )
            
            # 上报到监控系统
            response = requests.post(
                f"{settings.MONITORING_SERVICE_URL}/api/metrics",
                json={'service_id': service_id, 'metrics': metrics},
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Metrics reported for service {service_id}")
                return True
            else:
                logger.error(f"Failed to report metrics: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error reporting metrics: {e}")
            return False