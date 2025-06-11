from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from userdb.models import User, UserActivity
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_user_activities():
    """清理过期的用户活动记录"""
    try:
        # 删除30天前的活动记录
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = UserActivity.objects.filter(
            created_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"清理了 {deleted_count} 条过期的用户活动记录")
        return deleted_count
        
    except Exception as e:
        logger.error(f"清理用户活动记录失败: {str(e)}")
        raise


@shared_task
def sync_container_status():
    """同步用户容器状态"""
    try:
        from ..container_management.services import ContainerService
        container_service = ContainerService()
        
        active_users = User.objects.filter(
            status='active',
            container_id__isnull=False
        )
        
        updated_count = 0
        for user in active_users:
            try:
                status_info = container_service.get_container_status(user.container_id)
                if status_info and status_info.get('status') != user.container_status:
                    user.container_status = status_info.get('status')
                    user.save()
                    updated_count += 1
            except Exception as e:
                logger.warning(f"同步用户 {user.username} 容器状态失败: {str(e)}")
                continue
        
        logger.info(f"同步了 {updated_count} 个用户的容器状态")
        return updated_count
        
    except Exception as e:
        logger.error(f"同步容器状态失败: {str(e)}")
        raise


@shared_task
def generate_user_report():
    """生成用户统计报告"""
    try:
        total_users = User.objects.exclude(status='deleted').count()
        active_users = User.objects.filter(status='active').count()
        inactive_users = User.objects.filter(status='inactive').count()
        suspended_users = User.objects.filter(status='suspended').count()
        
        # 最近7天新注册用户
        seven_days_ago = timezone.now() - timedelta(days=7)
        new_users = User.objects.filter(
            created_at__gte=seven_days_ago
        ).exclude(status='deleted').count()
        
        # 最近7天活跃用户
        recent_activities = UserActivity.objects.filter(
            created_at__gte=seven_days_ago,
            action='login'
        ).values('user').distinct().count()
        
        report = {
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'suspended_users': suspended_users,
            'new_users_last_7_days': new_users,
            'active_users_last_7_days': recent_activities,
            'generated_at': timezone.now().isoformat()
        }
        
        logger.info(f"用户统计报告: {report}")
        return report
        
    except Exception as e:
        logger.error(f"生成用户报告失败: {str(e)}")
        raise