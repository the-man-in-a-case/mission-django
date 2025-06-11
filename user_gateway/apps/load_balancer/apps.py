from django.apps import AppConfig


class LoadBalancerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.load_balancer'
    verbose_name = '负载均衡管理'
