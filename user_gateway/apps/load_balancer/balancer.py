from django.db.models import F
from .models import RouteRegistry, LoadBalancerConfig
from ..userdb.models import ContainerInstance
import hashlib  # 新增导入
from django.core.cache import cache  # 新增导入

class LoadBalancer:
    # 类级策略注册表
    strategy_registry = {}
    
    # 策略注册装饰器
    @classmethod
    def register_strategy(cls, name):
        def decorator(func):
            if name in cls.strategy_registry:
                raise ValueError(f"Strategy '{name}' already registered")
            cls.strategy_registry[name] = func
            return func
        return decorator
    
    def __init__(self, route_registry: RouteRegistry):
        self.route = route_registry
        self.config = route_registry.load_balancer_config
        self.strategy = route_registry.load_balance_strategy
        # 初始化轮询计数器
        self.round_robin_counter = 0  # 新增

    # 使用装饰器注册策略
    @register_strategy('round_robin')
    def _round_robin(self, instances):
        """轮询策略（使用计数器实现真正轮询）"""
        if not instances:  # 新增防御性检查
            raise RuntimeError("No instances available for round_robin strategy")
        # 使用计数器取模实现轮询
        selected_index = self.round_robin_counter % len(instances)
        self.round_robin_counter += 1
        return instances[selected_index]

    @register_strategy('least_conn')
    def _least_connections(self, instances):
        """最少连接策略"""
        if not instances:  # 新增
            raise RuntimeError("No instances available for least_connections strategy")
        return instances.order_by('current_connections').first()

    def _weighted(self, instances):
        """权重策略"""
        if not instances:  # 新增
            raise RuntimeError("No instances available for weighted strategy")
        total_weight = sum(inst.weight for inst in instances)
        random_weight = random.randint(0, total_weight)
        current = 0
        for inst in instances:
            current += inst.weight
            if current >= random_weight:
                return inst
        return instances.first()  # 兜底

    def _ip_hash(self, instances):
        """IP哈希策略（支持配置哈希算法）"""
        if not instances:  # 新增防御性检查
            raise RuntimeError("No instances available for ip_hash strategy")
        # 从配置获取哈希算法，默认为md5
        hash_algorithm = self.config.ip_hash_algorithm or 'md5'
        # 获取真实客户端IP（实际应用需从请求上下文获取）
        client_ip = self._get_client_ip()  # 需要实现此方法
        
        # 使用指定算法计算哈希
        hash_obj = hashlib.new(hash_algorithm)
        hash_obj.update(client_ip.encode('utf-8'))
        hash_value = int(hash_obj.hexdigest(), 16)
        return instances[hash_value % len(instances)]

    def _response_time(self, instances):
        """响应时间策略"""
        if not instances:  # 新增
            raise RuntimeError("No instances available for response_time strategy")
        return instances.order_by('health_records__response_time').first()

    def select_instance(self) -> ContainerInstance:
        """根据负载均衡策略选择目标容器实例"""
        # 缓存键设计：包含路由ID确保唯一性
        cache_key = f"healthy_instances_{self.route.id}"
        healthy_instances = cache.get(cache_key)
        
        if not healthy_instances:
            # 使用select_related优化关联查询
            healthy_instances = list(ContainerInstance.objects.filter(
                container=self.route.container,
                is_healthy=True,
                status='running',
                current_connections__lt=F('max_connections')
            ).select_related('health_records'))  # 优化查询
            
            # 过滤熔断器不允许的实例
            filtered_instances = []
            for instance in healthy_instances:
                cb = CircuitBreaker(instance, self.config)
                if cb.allow_request():
                    filtered_instances.append(instance)
            healthy_instances = filtered_instances

            # 设置缓存，有效期5分钟（可配置）
            cache.set(cache_key, healthy_instances, timeout=300)
        
        if not healthy_instances:
            raise RuntimeError("No healthy instances available")
        
        # 添加默认策略避免KeyError
        selector = {
            'round_robin': self._round_robin,
            'least_conn': self._least_connections,
            'weighted': self._weighted,
            'ip_hash': self._ip_hash,
            'response_time': self._response_time
        }.get(self.strategy, self._round_robin)  # 使用get方法设置默认值
        
        return selector(healthy_instances)
        # 使用注册的策略
        selector = self.strategy_registry.get(self.strategy, self._round_robin)
