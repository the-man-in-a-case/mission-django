from django.utils import timezone
from django.core.cache import cache
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
        self.cache_key = f"circuit_breaker_{instance.id}"
        
        # 从缓存加载状态
        cached_state = cache.get(self.cache_key)
        if cached_state:
            self.state = cached_state['state']
            self.failure_count = cached_state['failure_count']
            self.last_failure_time = cached_state.get('last_failure_time')
            self.recovery_time = cached_state.get('recovery_time')
        else:
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0
            self.last_failure_time = None
            self.recovery_time = None

    def _save_state(self):
        """保存状态到缓存"""
        state = {
            'state': self.state,
            'failure_count': self.failure_count,
            'last_failure_time': self.last_failure_time,
            'recovery_time': self.recovery_time
        }
        cache.set(self.cache_key, state, timeout=self.config.recovery_timeout * 2)

    def record_failure(self):
        """记录失败请求"""
        if self.state == CircuitBreakerState.CLOSED:
            self.failure_count += 1
            self.last_failure_time = timezone.now()
            
            if self.failure_count >= self.config.failure_threshold:
                self._open()
        self._save_state()

    def record_success(self):
        """记录成功请求"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self._close()
        self._save_state()

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
        self.instance.mark_unhealthy()
        self._save_state()

    def _close(self):
        """关闭熔断（恢复正常）"""
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.instance.mark_healthy()
        self._save_state()