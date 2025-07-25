from celery import shared_task
from .services import ExceptionCollectorService
import logging
import psutil
import docker

logger = logging.getLogger(__name__)

@shared_task
def collect_exceptions_task():
    """收集异常数据的定时任务"""
    collector = ExceptionCollectorService()
    count = collector.collect_all_exceptions()
    logger.info(f"收集异常任务完成，共收集 {count} 条")
    return count

@shared_task
def report_exceptions_task():
    """上报异常数据的定时任务"""
    collector = ExceptionCollectorService()
    count = collector.report_unreported_exceptions()
    logger.info(f"上报异常任务完成，共上报 {count} 条")
    return count

@shared_task
def report_health_metrics_task():
    """上报健康指标任务（修复硬编码）"""
    from .registry_client import GatewayRegistryClient
    from .models import ServiceInstance
    
    client = GatewayRegistryClient()
    
    # 获取容器实际指标
    try:
        docker_client = docker.from_env()
        for instance in ServiceInstance.objects.filter(health_status='healthy'):
            try:
                container = docker_client.containers.get(instance.container_id)
                stats = container.stats(stream=False)
                
                # 计算实际资源使用率
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']
                cpu_usage = (cpu_delta / system_delta) * 100.0 if system_delta > 0 else 0
                
                memory_usage = (stats['memory_stats']['usage'] / 
                               stats['memory_stats']['limit']) * 100.0
                
                metrics = {
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'disk_usage': psutil.disk_usage('/').percent,
                    'service_status': instance.health_status
                }
                client.report_metrics(metrics)
                
            except Exception as e:
                logger.error(f"获取容器{instance.container_id}指标失败: {e}")
                
    except Exception as e:
        logger.error(f"Docker连接失败，使用系统指标: {e}")
        # 回退到系统指标
        for instance in ServiceInstance.objects.filter(health_status='healthy'):
            metrics = {
                'cpu_usage': psutil.cpu_percent(),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'service_status': instance.health_status
            }
            client.report_metrics(metrics)
    
    logger.info("健康指标上报任务完成")
    return True