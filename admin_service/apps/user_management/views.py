from django.shortcuts import render

# Create your views here.
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import User, UserActivity
from .serializers import (
    UserSerializer, UserListSerializer, UserActivitySerializer, LoginSerializer
)
from .services import UserService
from .permissions import IsAdminOrReadOnly
from common.exceptions import APIException

import logging

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    """用户管理视图集"""
    queryset = User.objects.exclude(status='deleted')
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return UserListSerializer
        return UserSerializer
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = UserService()
    
    def create(self, request):
        """创建用户"""
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            user = self.user_service.create_user(serializer.validated_data)
            # 新增：生成用户Token
            token, _ = Token.objects.get_or_create(user=user)
            response_serializer = UserSerializer(user)
            
            return Response(
                {
                    'success': True,
                    'data': {
                        'user': response_serializer.data,
                        'token': token.key  # 返回Token
                    },
                    'message': '用户创建成功'
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @method_decorator(cache_page(60 * 5))  # 缓存5分钟
    def list(self, request):
        """获取用户列表"""
        try:
            # 获取查询参数
            filters = {}
            if request.query_params.get('status'):
                filters['status'] = request.query_params.get('status')
            if request.query_params.get('permission_level'):
                filters['permission_level'] = request.query_params.get('permission_level')
            if request.query_params.get('search'):
                filters['search'] = request.query_params.get('search')
            
            users = self.user_service.get_users_list(filters)
            
            # 分页
            page = self.paginate_queryset(users)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response({
                    'success': True,
                    'data': serializer.data
                })
            
            serializer = self.get_serializer(users, many=True)
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, pk=None):
        """获取单个用户详情"""
        try:
            user = self.user_service.get_user_by_id(pk)
            if not user:
                return Response(
                    {
                        'success': False,
                        'message': '用户不存在'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(user)
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"获取用户详情失败: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, pk=None):
        """更新用户信息"""
        try:
            user = self.user_service.get_user_by_id(pk)
            if not user:
                return Response(
                    {
                        'success': False,
                        'message': '用户不存在'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
            
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            
            updated_user = self.user_service.update_user(pk, serializer.validated_data)
            response_serializer = UserSerializer(updated_user)
            
            return Response({
                'success': True,
                'data': response_serializer.data,
                'message': '用户更新成功'
            })
            
        except Exception as e:
            logger.error(f"更新用户失败: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    def destroy(self, request, pk=None):
        """删除用户"""
        try:
            result = self.user_service.delete_user(pk)
            if result:
                return Response({
                    'success': True,
                    'message': '用户删除成功'
                })
            else:
                return Response(
                    {
                        'success': False,
                        'message': '删除用户失败'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def manage_container(self, request, pk=None):
        """管理用户容器"""
        try:
            action_type = request.data.get('action')
            if action_type not in ['start', 'stop', 'restart']:
                return Response(
                    {
                        'success': False,
                        'message': '无效的操作类型'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            result = self.user_service.manage_user_container(pk, action_type)
            
            return Response({
                'success': True,
                'data': result,
                'message': f'容器{action_type}操作成功'
            })
            
        except Exception as e:
            logger.error(f"管理用户容器失败: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """获取用户活动记录"""
        try:
            limit = int(request.query_params.get('limit', 50))
            activities = self.user_service.get_user_activities(pk, limit)
            
            serializer = UserActivitySerializer(activities, many=True)
            return Response({
                'success': True,
                'data': serializer.data
            })
            
        except Exception as e:
            logger.error(f"获取用户活动记录失败: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AuthViewSet(viewsets.ViewSet):
    """认证视图集"""
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        """用户登录"""
        try:
            serializer = LoginSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            user = serializer.validated_data['user']
            login(request, user)
            
            # 创建或获取token
            token, created = Token.objects.get_or_create(user=user)
            
            # 更新最后登录时间
            user.last_login_at = timezone.now()
            user.save()
            
            # 记录登录活动
            UserActivity.objects.create(
                user=user,
                action='login',
                description='用户登录',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return Response({
                'success': True,
                'data': {
                    'token': token.key,
                    'user': UserSerializer(user).data
                },
                'message': '登录成功'
            })
            
        except Exception as e:
            logger.error(f"用户登录失败: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['post'])
    def logout(self, request):
        """用户登出"""
        try:
            if request.user.is_authenticated:
                # 记录登出活动
                UserActivity.objects.create(
                    user=request.user,
                    action='logout',
                    description='用户登出',
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                # 删除token
                try:
                    token = Token.objects.get(user=request.user)
                    token.delete()
                except Token.DoesNotExist:
                    pass
                
                logout(request)
            
            return Response({
                'success': True,
                'message': '登出成功'
            })
            
        except Exception as e:
            logger.error(f"用户登出失败: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='get-token')
    def get_token(self, request):
        """获取当前用户的Token"""
        user = request.user
        if not user.is_authenticated:
            return Response({'error': '用户未登录'}, status=status.HTTP_401_UNAUTHORIZED)

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'success': True,
            'data': {
                'token': token.key,
                'user_id': user.id,
                'username': user.username
            }
        })
