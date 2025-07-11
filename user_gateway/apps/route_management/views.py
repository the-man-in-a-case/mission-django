from django.shortcuts import render

# Create your views here.
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db import transaction
import logging

from userdb.models import ContainerRegistry, RouteMetrics
from .serializers import (
    ContainerRegistrySerializer, 
    ContainerRegistryCreateSerializer,
    RouteMetricsSerializer
)
from .route_manager import RouteManager, K8sRouteManager
from .services import RouteManagementService
from common.permissions import IsGatewayService

logger = logging.getLogger(__name__)


class ContainerRegistryViewSet(viewsets.ModelViewSet):
    """容器注册表管理API"""
    queryset = ContainerRegistry.objects.all()
    serializer_class = ContainerRegistrySerializer
    permission_classes = [IsGatewayService]
    lookup_field = 'user_id'

    def get_serializer_class(self):
        if self.action == 'create':
            return ContainerRegistryCreateSerializer
        return ContainerRegistrySerializer

    @action(detail=True, methods=['post'])
    def register(self, request, user_id=None):
        """注册用户容器"""
        try:
            service = RouteManagementService()
            data = request.data.copy()
            data['user_id'] = user_id
            
            registry = service.register_container(data)
            serializer = ContainerRegistrySerializer(registry)
            
            logger.info(f"Container registered for user {user_id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Failed to register container for user {user_id}: {str(e)}")
            return Response(
                {'error': 'Container registration failed', 'detail': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'])
    def unregister(self, request, user_id=None):
        """注销用户容器"""
        try:
            service = RouteManagementService()
            service.unregister_container(user_id)
            
            logger.info(f"Container unregistered for user {user_id}")
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except ContainerRegistry.DoesNotExist:
            return Response(
                {'error': 'Container not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def health_check(self, request, user_id=None):
        """手动触发健康检查"""
        try:
            service = RouteManagementService()
            result = service.check_container_health(user_id)
            
            return Response({
                'user_id': user_id,
                'is_healthy': result,
                'checked_at': timezone.now()
            })
            
        except ContainerRegistry.DoesNotExist:
            return Response(
                {'error': 'Container not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def route_info(self, request, pk=None):
        """获取路由信息"""
        tenant_id = pk  # 这里 pk 就是 tenant_id，因为 DRF 默认用 pk 作为主键参数
        try:
            route_manager = K8sRouteManager()
            target_url, route_info = route_manager.route_request(tenant_id, request.data)
            if not target_url:
                return Response(
                    {'error': 'Container not available', **route_info},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response({'target_url': target_url, **route_info})
        except Exception as e:
            logger.error(f"Failed to get route info for tenant {tenant_id}: {str(e)}")
            return Response(
                {'error': 'Failed to get route information'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def health_status(self, request):
        """获取所有容器健康状态"""
        queryset = self.get_queryset()
        healthy_count = queryset.filter(is_healthy=True).count()
        total_count = queryset.count()
        
        return Response({
            'total_containers': total_count,
            'healthy_containers': healthy_count,
            'unhealthy_containers': total_count - healthy_count,
            'health_rate': round((healthy_count / total_count * 100), 2) if total_count > 0 else 0
        })


class RouteMetricsViewSet(viewsets.ReadOnlyModelViewSet):
    """路由指标API"""
    queryset = RouteMetrics.objects.all()
    serializer_class = RouteMetricsSerializer
    permission_classes = [IsGatewayService]
    lookup_field = 'user_id'

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """获取路由指标汇总"""
        metrics = RouteMetrics.objects.all()
        
        total_requests = sum(m.total_requests for m in metrics)
        total_successful = sum(m.successful_requests for m in metrics)
        total_failed = sum(m.failed_requests for m in metrics)
        
        return Response({
            'total_users': metrics.count(),
            'total_requests': total_requests,
            'successful_requests': total_successful,
            'failed_requests': total_failed,
            'overall_success_rate': round((total_successful / total_requests * 100), 2) if total_requests > 0 else 0
        })


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            token, created = Token.objects.get_or_create(user=user)
            
            # 设置Token过期时间
            if not created:
                # 如果Token已存在且过期则刷新
                if token.expires_at and token.expires_at < timezone.now():
                    token.key = Token.generate_key()
            token.expires_at = timezone.now() + timezone.timedelta(days=settings.TOKEN_EXPIRATION_DAYS)
            token.save()
            
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'email': user.email,
                'expires_at': token.expires_at
            })
        except Exception as e:
            return Response({
                'error': 'Authentication failed',
                'detail': str(e)
            }, status=status.HTTP_401_UNAUTHORIZED)