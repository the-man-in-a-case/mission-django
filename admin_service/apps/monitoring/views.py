from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.userdb.models import UserContainer, ContainerInstance, RouteMetrics
from .models import AlertRule
from .serializers import (
    ContainerMetricsSerializer, InstanceHealthSerializer,
    RoutePerformanceSerializer, AlertRuleSerializer
)

class ContainerMonitoringViewSet(viewsets.ReadOnlyModelViewSet):
    """用户容器监控视图集"""
    permission_classes = [IsAuthenticated]
    serializer_class = ContainerMetricsSerializer

    def get_queryset(self):
        # 可根据用户权限过滤容器（示例：管理员查看所有，普通用户查看自己的）
        if self.request.user.is_superuser:
            return UserContainer.objects.all()
        return UserContainer.objects.filter(user=self.request.user)

class InstanceHealthViewSet(viewsets.ReadOnlyModelViewSet):
    """容器实例健康状态视图集"""
    permission_classes = [IsAuthenticated]
    serializer_class = InstanceHealthSerializer

    def get_queryset(self):
        container_id = self.request.query_params.get('container_id')
        queryset = ContainerInstance.objects.all()
        if container_id:
            queryset = queryset.filter(container_id=container_id)
        return queryset

class RoutePerformanceView(viewsets.ReadOnlyModelViewSet):
    """路由性能指标视图"""
    permission_classes = [IsAuthenticated]
    serializer_class = RoutePerformanceSerializer
    queryset = RouteMetrics.objects.all()

class AlertRuleViewSet(viewsets.ModelViewSet):
    """警报规则管理视图集"""
    permission_classes = [IsAuthenticated]
    serializer_class = AlertRuleSerializer
    queryset = AlertRule.objects.all()
