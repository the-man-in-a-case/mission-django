from rest_framework import serializers
from .models import UserContainer, ContainerInstance

class UserContainerSerializer(serializers.ModelSerializer):
    """用户容器主信息序列化器"""
    class Meta:
        model = UserContainer
        fields = [
            'id', 'user', 'container_name', 'deployment_name', 'service_name',
            'status', 'cpu_limit', 'memory_limit', 'storage_limit', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class ContainerInstanceSerializer(serializers.ModelSerializer):
    """容器实例详情序列化器"""
    class Meta:
        model = ContainerInstance
        fields = ['id', 'container', 'instance_id', 'pod_name', 'pod_ip', 'port']
        read_only_fields = ['id']

