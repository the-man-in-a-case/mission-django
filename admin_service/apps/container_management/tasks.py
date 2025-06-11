from celery import shared_task
from .services import ContainerService
from ..userdb.models import UserContainer

@shared_task
def monitor_container_status():
    """定期监控所有容器状态"""
    for container in UserContainer.objects.all():
        ContainerService.get_container_status(container.id)
    return "容器状态监控完成"

