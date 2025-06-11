from rest_framework import serializers
from django.utils import timezone
from userdb.models import (
    UserContainer, ContainerInstance, RouteRegistry, LoadBalancerConfig,
    RouteMetrics, RouteLog, HealthCheckRecord, GatewayNode
)


class UserContainerSerializer(serializers.ModelSerializer):
    """用户容器序列化器"""
    service_url = serializers.ReadOnlyField()
    is_ready = serializers.ReadOnlyField()
    uptime = serializers.SerializerMethodField()
    
    class Meta:
        model = UserContainer
        fields = [
            'id', 'user_id', 'container_name', 'deployment_name', 'service_name',
            'namespace', 'cluster_ip', 'external_ip', 'port',
            'status', 'replicas', 'ready_replicas',
            'cpu_request', 'memory_request', 'cpu_limit', 'memory_limit', 'storage_size',
            'created_at', 'updated_at', 'last_accessed',
            'labels', 'annotations', 'environment_vars',
            'service_url', 'is_ready', 'uptime'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_uptime(self, obj):
        """获取容器运行时间"""
        if obj.status == 'running' and obj.created_at:
            delta = timezone.now() - obj.created_at
            return delta.total_seconds()
        return 0


class UserContainerCreateSerializer(serializers.ModelSerializer):
    """用户容器创建序列化器"""
    
    class Meta:
        model = UserContainer
        fields = [
            'user_id', 'container_name', 'port',
            'cpu_request', 'memory_request', 'cpu_limit', 'memory_limit', 'storage_size',
            'labels', 'annotations', 'environment_vars'
        ]
    
    def validate_user_id(self, value):
        """验证用户ID是否已存在"""
        if UserContainer.objects.filter(user_id=value).exists():
            raise serializers.ValidationError(f"用户 {value} 的容器已存在")
        return value
    
    def create(self, validated_data):
        """创建用户容器"""
        user_id = validated_data['user_id']
        
        # 设置默认值
        validated_data.setdefault('deployment_name', f'user-{user_id}')
        validated_data.setdefault('service_name', f'user-{user_id}-service')
        validated_data.setdefault('namespace', 'user-containers')
        validated_data.setdefault('container_name', f'container-{user_id}')
        
        return super().create(validated_data)


class UserContainerUpdateSerializer(serializers.ModelSerializer):
    """用户容器更新序列化器"""
    
    class Meta:
        model = UserContainer
        fields = [
            'status', 'cluster_ip', 'external_ip', 'replicas', 'ready_replicas',
            'cpu_request', 'memory_request', 'cpu_limit', 'memory_limit',
            'labels', 'annotations', 'environment_vars'
        ]
    
    def update(self, instance, validated_data):
        """更新容器信息"""
        return super().update(instance, validated_data)


class ContainerInstanceSerializer(serializers.ModelSerializer):
    """容器实例序列化器"""
    service_url = serializers.ReadOnlyField()
    is_available = serializers.ReadOnlyField()
    container_info = UserContainerSerializer(source='container', read_only=True)
    
    class Meta:
        model = ContainerInstance
        fields = [
            'id', 'container', 'container_info', 'instance_id', 'pod_name',
            'pod_ip', 'port', 'status', 'is_healthy', 'consecutive_failures',
            'weight', 'current_connections', 'health_check_url', 'last_health_check',
            'created_at', 'updated_at', 'service_url', 'is_available'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContainerInstanceCreateSerializer(serializers.ModelSerializer):
    """容器实例创建序列化器"""
    
    class Meta:
        model = ContainerInstance
        fields = [
            'container', 'instance_id', 'pod_name', 'pod_ip', 'port',
            'weight', 'health_check_url'
        ]


class RouteRegistrySerializer(serializers.ModelSerializer):
    """路由注册表序列化器"""
    container_info = UserContainerSerializer(source='container', read_only=True)
    
    class Meta:
        model = RouteRegistry
        fields = [
            'id', 'user_id', 'container', 'container_info',
            'route_path', 'target_service', 'target_namespace',
            'load_balance_strategy', 'health_check_enabled', 'health_check_path',
            'health_check_interval', 'health_check_timeout', 'max_failures',
            'is_active', 'last_route_time', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RouteRegistryCreateSerializer(serializers.ModelSerializer):
    """路由注册表创建序列化器"""
    
    class Meta:
        model = RouteRegistry
        fields = [
            'user_id', 'container', 'route_path', 'target_service', 'target_namespace',
            'load_balance_strategy', 'health_check_enabled', 'health_check_path',
            'health_check_interval', 'health_check_timeout', 'max_failures'
        ]
    
    def validate_user_id(self, value):
        """验证用户ID是否已存在"""
        if RouteRegistry.objects.filter(user_id=value).exists():
            raise serializers.ValidationError(f"用户 {value} 的路由已存在")
        return value


class LoadBalancerConfigSerializer(serializers.ModelSerializer):
    """负载均衡器配置序列化器"""
    route_info = RouteRegistrySerializer(source='route_registry', read_only=True)
    
    class Meta:
        model = LoadBalancerConfig
        fields = [
            'id', 'route_registry', 'route_info',
            'max_connections', 'connection_timeout', 'idle_timeout',
            'retry_attempts', 'retry_delay',
            'circuit_breaker_enabled', 'failure_threshold', 'recovery_timeout',
            'rate_limit_enabled', 'requests_per_minute',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class RouteMetricsSerializer(serializers.ModelSerializer):
    """路由指标序列化器"""
    success_rate = serializers.ReadOnlyField()
    route_info = RouteRegistrySerializer(source='route_registry', read_only=True)
    
    class Meta:
        model = RouteMetrics
        fields = [
            'id', 'route_registry', 'route_info',
            'total_requests', 'successful_requests', 'failed_requests',
            'avg_response_time', 'min_response_time', 'max_response_time',
            'timeout_count', 'connection_error_count', 'server_error_count',
            'last_request_time', 'reset_time', 'updated_at', 'success_rate'
        ]
        read_only_fields = ['id', 'reset_time', 'updated_at']


class RouteLogSerializer(serializers.ModelSerializer):
    """路由日志序列化器"""
    route_info = RouteRegistrySerializer(source='route_registry', read_only=True)
    instance_info = ContainerInstanceSerializer(source='container_instance', read_only=True)
    
    class Meta:
        model = RouteLog
        fields = [
            'id', 'route_registry', 'route_info', 'container_instance', 'instance_info',
            'request_id', 'request_method', 'request_path', 'request_headers',
            'client_ip', 'user_agent', 'target_url', 'load_balance_strategy',
            'response_status', 'response_time', 'response_size',
            'error_type', 'error_message', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class RouteLogCreateSerializer(serializers.ModelSerializer):
    """路由日志创建序列化器"""
    
    class Meta:
        model = RouteLog
        fields = [
            'route_registry', 'container_instance', 'request_id',
            'request_method', 'request_path', 'request_headers',
            'client_ip', 'user_agent', 'target_url', 'load_balance_strategy',
            'response_status', 'response_time', 'response_size',
            'error_type', 'error_message'
        ]


class HealthCheckRecordSerializer(serializers.ModelSerializer):
    """健康检查记录序列化器"""
    instance_info = ContainerInstanceSerializer(source='container_instance', read_only=True)
    
    class Meta:
        model = HealthCheckRecord
        fields = [
            'id', 'container_instance', 'instance_info',
            'is_healthy', 'response_time', 'status_code',
            'check_url', 'error_message', 'details', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class HealthCheckRecordCreateSerializer(serializers.ModelSerializer):
    """健康检查记录创建序列化器"""
    
    class Meta:
        model = HealthCheckRecord
        fields = [
            'container_instance', 'is_healthy', 'response_time', 'status_code',
            'check_url', 'error_message', 'details'
        ]


class GatewayNodeSerializer(serializers.ModelSerializer):
    """网关节点序列化器"""
    is_healthy = serializers.ReadOnlyField()
    
    class Meta:
        model = GatewayNode
        fields = [
            'id', 'node_id', 'hostname', 'ip_address', 'port',
            'is_active', 'cpu_usage', 'memory_usage',
            'current_connections', 'total_requests',
            'last_heartbeat', 'created_at', 'is_healthy'
        ]
        read_only_fields = ['id', 'created_at', 'last_heartbeat']


class GatewayNodeCreateSerializer(serializers.ModelSerializer):
    """网关节点创建序列化器"""
    
    class Meta:
        model = GatewayNode
        fields = [
            'node_id', 'hostname', 'ip_address', 'port'
        ]
    
    def validate_node_id(self, value):
        """验证节点ID是否已存在"""
        if GatewayNode.objects.filter(node_id=value).exists():
            raise serializers.ValidationError(f"节点 {value} 已存在")
        return value


class ContainerStatusSerializer(serializers.Serializer):
    """容器状态序列化器"""
    user_id = serializers.CharField()
    status = serializers.CharField()
    is_ready = serializers.BooleanField()
    replicas = serializers.IntegerField()
    ready_replicas = serializers.IntegerField()
    service_url = serializers.CharField(allow_null=True)
    last_accessed = serializers.DateTimeField(allow_null=True)
    uptime = serializers.FloatField()


class RouteStatisticsSerializer(serializers.Serializer):
    """路由统计序列化器"""
    total_containers = serializers.IntegerField()
    running_containers = serializers.IntegerField()
    healthy_containers = serializers.IntegerField()
    total_requests = serializers.IntegerField()
    error_rate = serializers.FloatField()
    avg_response_time = serializers.FloatField()
    
    # 按时间统计
    hourly_stats = serializers.DictField()
    daily_stats = serializers.DictField()


class BatchContainerOperationSerializer(serializers.Serializer):
    """批量容器操作序列化器"""
    user_ids = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=False,
        help_text="用户ID列表"
    )
    operation = serializers.ChoiceField(
        choices=['start', 'stop', 'restart', 'delete'],
        help_text="操作类型"
    )
    force = serializers.BooleanField(
        default=False,
        help_text="是否强制执行"
    )
    
    def validate_user_ids(self, value):
        """验证用户ID列表"""
        if len(value) > 100:
            raise serializers.ValidationError("一次最多只能操作100个容器")
        
        # 检查容器是否存在
        existing_containers = UserContainer.objects.filter(
            user_id__in=value
        ).values_list('user_id', flat=True)
        
        missing_users = set(value) - set(existing_containers)
        if missing_users:
            raise serializers.ValidationError(
                f"以下用户的容器不存在: {list(missing_users)}"
            )
        
        return value


class InstanceHealthStatusSerializer(serializers.Serializer):
    """实例健康状态序列化器"""
    instance_id = serializers.CharField()
    pod_name = serializers.CharField()
    status = serializers.CharField()
    is_healthy = serializers.BooleanField()
    consecutive_failures = serializers.IntegerField()
    last_health_check = serializers.DateTimeField(allow_null=True)
    response_time = serializers.FloatField(allow_null=True)


class LoadBalancerStatusSerializer(serializers.Serializer):
    """负载均衡器状态序列化器"""
    user_id = serializers.CharField()
    total_instances = serializers.IntegerField()
    healthy_instances = serializers.IntegerField()
    current_strategy = serializers.CharField()
    total_connections = serializers.IntegerField()
    instances = InstanceHealthStatusSerializer(many=True)


class SystemMetricsSerializer(serializers.Serializer):
    """系统指标序列化器"""
    total_containers = serializers.IntegerField()
    running_containers = serializers.IntegerField()
    pending_containers = serializers.IntegerField()
    error_containers = serializers.IntegerField()
    total_instances = serializers.IntegerField()
    healthy_instances = serializers.IntegerField()
    total_routes = serializers.IntegerField()
    active_routes = serializers.IntegerField()
    gateway_nodes = serializers.IntegerField()
    healthy_gateway_nodes = serializers.IntegerField()


class RouteMetricsUpdateSerializer(serializers.Serializer):
    """路由指标更新序列化器"""
    response_time = serializers.FloatField(min_value=0)
    success = serializers.BooleanField(default=True)
    error_type = serializers.ChoiceField(
        choices=['timeout', 'connection', 'server'],
        required=False,
        allow_null=True
    )
    
    def validate(self, data):
        """验证数据"""
        if not data.get('success') and not data.get('error_type'):
            raise serializers.ValidationError(
                "失败请求必须指定错误类型"
            )
        return data