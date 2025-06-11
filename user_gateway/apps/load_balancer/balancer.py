from django.db.models import F
from .models import RouteRegistry, LoadBalancerConfig
from ..userdb.models import ContainerInstance

class LoadBalancer:
    def __init__(self, route_registry: RouteRegistry):
        self.route = route_registry
        self.config = route_registry.load_balancer_config
        self.strategy = route_registry.load_balance_strategy

    def select_instance(self) -> ContainerInstance:
        """根据负载均衡策略选择目标容器实例"""
        healthy_instances = ContainerInstance.objects.filter(
            container=self.route.container,
            is_healthy=True,
            status='running',
            current_connections__lt=F('max_connections')  # 未达最大连接数
        )

        if not healthy_instances.exists():
            raise RuntimeError("No healthy instances available")

        selector = {
            'round_robin': self._round_robin,
            'least_conn': self._least_connections,
            'weighted': self._weighted,
            'ip_hash': self._ip_hash,
            'response_time': self._response_time
        }[self.strategy]

        return selector(healthy_instances)

    def _round_robin(self, instances):
        """轮询策略（简单实现：按创建时间排序循环）"""
        return instances.order_by('created_at').first()

    def _least_connections(self, instances):
        """最少连接策略"""
        return instances.order_by('current_connections').first()

    def _weighted(self, instances):
        """权重策略（权重越高被选中概率越大）"""
        total_weight = sum(inst.weight for inst in instances)
        random_weight = random.randint(0, total_weight)
        current = 0
        for inst in instances:
            current += inst.weight
            if current >= random_weight:
                return inst
        return instances.first()  # 兜底

    def _ip_hash(self, instances):
        """IP哈希策略（需要从请求中获取客户端IP）"""
        # 实际使用时需要从request中获取client_ip
        client_ip = "192.168.1.100"  # 示例IP
        hash_value = hash(client_ip)
        return instances[hash_value % len(instances)]

    def _response_time(self, instances):
        """响应时间策略（选择平均响应时间最短的实例）"""
        return instances.order_by('health_records__response_time').first()