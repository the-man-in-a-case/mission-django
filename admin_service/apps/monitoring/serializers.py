from rest_framework import serializers
from apps.userdb.models import ContainerInstance, AlertRule

class ContainerMetricsSerializer(serializers.Serializer):
    cpu_usage = serializers.CharField(read_only=True)
    memory_usage = serializers.CharField(read_only=True)
    usage_percent = serializers.DictField(read_only=True)

class InstanceHealthSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContainerInstance
        fields = ['pod_name', 'status', 'is_healthy', 'consecutive_failures', 'last_health_check']

class AlertRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertRule
        fields = '__all__'
        extra_kwargs = {
            'container_id': {'required': True},
            'created_at': {'read_only': True}
        }