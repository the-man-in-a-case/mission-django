from django.conf import settings

class MonitoringConfig:
    """监控配置管理"""
    
    @staticmethod
    def get_redis_config():
        """获取 Redis 配置"""
        return {
            'host': getattr(settings, 'REDIS_HOST', 'redis'),
            'port': getattr(settings, 'REDIS_PORT', 6379),
            'db': getattr(settings, 'REDIS_DB', 0),
            'password': getattr(settings, 'REDIS_PASSWORD', None),
        }
    
    @staticmethod
    def get_influxdb_config():
        """获取 InfluxDB 配置"""
        return {
            'host': getattr(settings, 'INFLUXDB_HOST', 'influxdb'),
            'port': getattr(settings, 'INFLUXDB_PORT', 8086),
            'token': getattr(settings, 'INFLUXDB_TOKEN', None),
            'org': getattr(settings, 'INFLUXDB_ORG', None),
            'bucket': getattr(settings, 'INFLUXDB_BUCKET', None),
        }
    
    @staticmethod
    def get_rabbitmq_config():
        """获取 RabbitMQ 配置"""
        return {
            'host': getattr(settings, 'RABBITMQ_HOST', 'rabbitmq'),
            'port': getattr(settings, 'RABBITMQ_PORT', 5672),
            'username': getattr(settings, 'RABBITMQ_USERNAME', 'admin'),
            'password': getattr(settings, 'RABBITMQ_PASSWORD', 'password'),
        }