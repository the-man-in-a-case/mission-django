from django.utils import timezone
from .models import LoadBalancerConfig
from ..userdb.models import ContainerInstance

class CircuitBreakerState:
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

class CircuitBreaker:
    def __init__(self, instance: ContainerInstance, config: LoadBalancerConfig):
        self.instance = instance
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.recovery_time = None

    def record_failure(self):
        """记录失败请求"""
        if self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            self.last_failure_time = timezone.now()
            
            if self.failure_count >= self.config.failure_threshold:
                self._open()

    def record_success(self):
        """记录成功请求"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self._close()

    def allow_request(self) -> bool:
        """判断是否允许请求通过"""
        if self.state == CircuitBreakerState.CLOSED:
            return True
        
        if self.state == CircuitBreakerState.OPEN:
            if timezone.now() >= self.recovery_time:
                self.state = CircuitBreakerState.HALF_OPEN
                return True
            return False
        
        # HALF_OPEN状态允许部分请求测试恢复
        return True

    def _open(self):
        """开启熔断"""
        self.state = CircuitBreakerState.OPEN
        self.recovery_time = timezone.now() + timezone.timedelta(seconds=self.config.recovery_timeout)
        self.instance.mark_unhealthy()  # 关联容器实例健康状态

    def _close(self):
        """关闭熔断（恢复正常）"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.instance.mark_healthy()  # 关联容器实例健康状态