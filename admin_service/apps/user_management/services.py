import logging
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from .models import User, UserActivity
from ..container_management.services import ContainerService

logger = logging.getLogger(__name__)


class UserService:
    """用户服务类"""
    
    def __init__(self):
        self.container_service = ContainerService()
    
    @transaction.atomic
    def create_user(self, user_data: Dict) -> User:
        """创建用户并初始化容器"""
        try:
            # 1. 创建用户记录
            password = user_data.pop('password')
            # confirm_password = user_data.pop('confirm_password', None)
            
            user = User.objects.create_user(**user_data)
            user.set_password(password)
            user.save()
            
            # 2. 创建用户容器
            container_config = {
                'user_id': str(user.id),
                'cpu_limit': user.cpu_limit,
                'memory_limit': user.memory_limit,
                'storage_limit': user.storage_limit,
                'permission_level': user.permission_level
            }
            
            container_info = self.container_service.create_user_container(
                user.id, container_config
            )
            
            # 3. 更新用户容器信息
            user.container_id = container_info.get('container_id')
            user.container_status = container_info.get('status', 'creating')
            user.save()
            
            # 4. 记录用户活动
            self._log_user_activity(
                user=user,
                action='container_start',
                description=f'为用户 {user.username} 创建容器: {user.container_id}'
            )
            
            logger.info(f"成功创建用户 {user.username} 及其容器")
            return user
            
        except Exception as e:
            logger.error(f"创建用户失败: {str(e)}")
            raise Exception(f"创建用户失败: {str(e)}")
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """根据ID获取用户"""
        try:
            return User.objects.get(id=user_id, status__ne='deleted')
        except User.DoesNotExist:
            return None
    
    def get_users_list(self, filters: Dict = None) -> List[User]:
        """获取用户列表"""
        queryset = User.objects.exclude(status='deleted')
        
        if filters:
            if 'status' in filters:
                queryset = queryset.filter(status=filters['status'])
            if 'permission_level' in filters:
                queryset = queryset.filter(permission_level=filters['permission_level'])
            if 'search' in filters:
                search_term = filters['search']
                queryset = queryset.filter(
                    username__icontains=search_term
                ) | queryset.filter(
                    email__icontains=search_term
                )
        
        return queryset.order_by('-created_at')
    
    @transaction.atomic
    def update_user(self, user_id: str, update_data: Dict) -> User:
        """更新用户信息"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise Exception("用户不存在")
            
            # 更新用户基本信息
            for field, value in update_data.items():
                if field not in ['password', 'confirm_password'] and hasattr(user, field):
                    setattr(user, field, value)
            
            # 处理密码更新
            if 'password' in update_data:
                user.set_password(update_data['password'])
            
            user.save()
            
            # 如果资源配置发生变化，更新容器
            resource_fields = ['cpu_limit', 'memory_limit', 'storage_limit']
            if any(field in update_data for field in resource_fields):
                self._update_container_resources(user)
            
            logger.info(f"成功更新用户 {user.username}")
            return user
            
        except Exception as e:
            logger.error(f"更新用户失败: {str(e)}")
            raise Exception(f"更新用户失败: {str(e)}")
    
    @transaction.atomic
    def delete_user(self, user_id: str) -> bool:
        """删除用户并销毁容器"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise Exception("用户不存在")
            
            # 1. 销毁用户容器
            if user.container_id:
                self.container_service.destroy_user_container(user.id)
            
            # 2. 标记用户为已删除（软删除）
            user.status = 'deleted'
            user.container_status = 'destroyed'
            user.save()
            
            # 3. 记录用户活动
            self._log_user_activity(
                user=user,
                action='container_stop',
                description=f'删除用户 {user.username} 及其容器'
            )
            
            logger.info(f"成功删除用户 {user.username}")
            return True
            
        except Exception as e:
            logger.error(f"删除用户失败: {str(e)}")
            raise Exception(f"删除用户失败: {str(e)}")
    
    def manage_user_container(self, user_id: str, action: str) -> Dict:
        """管理用户容器（启动/停止/重启）"""
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                raise Exception("用户不存在")
            
            result = self.container_service.manage_container(user.container_id, action)
            
            # 更新容器状态
            user.container_status = result.get('status', user.container_status)
            user.save()
            
            # 记录活动
            self._log_user_activity(
                user=user,
                action=f'container_{action}',
                description=f'对用户 {user.username} 的容器执行 {action} 操作'
            )
            
            return result
            
        except Exception as e:
            logger.error(f"管理用户容器失败: {str(e)}")
            raise Exception(f"管理用户容器失败: {str(e)}")
    
    def get_user_activities(self, user_id: str, limit: int = 50) -> List[UserActivity]:
        """获取用户活动记录"""
        return UserActivity.objects.filter(
            user_id=user_id
        ).order_by('-created_at')[:limit]
    
    def _update_container_resources(self, user: User):
        """更新容器资源配置"""
        try:
            resource_config = {
                'cpu_limit': user.cpu_limit,
                'memory_limit': user.memory_limit,
                'storage_limit': user.storage_limit
            }
            self.container_service.update_container_resources(
                user.container_id, resource_config
            )
        except Exception as e:
            logger.error(f"更新容器资源失败: {str(e)}")
    
    def _log_user_activity(self, user: User, action: str, description: str = '', 
                          ip_address: str = None, user_agent: str = None):
        """记录用户活动"""
        UserActivity.objects.create(
            user=user,
            action=action,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent
        )