from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .services import ContainerService
from .serializers import UserContainerSerializer, ContainerInstanceSerializer
from ..userdb.models import UserContainer

class ContainerManagementViewSet(viewsets.GenericViewSet):
    queryset = UserContainer.objects.all()
    serializer_class = UserContainerSerializer  # 使用新增的序列化器

    @action(detail=False, methods=["post"], url_path="create")
    def create_container(self, request):
        """创建用户容器"""
        user_id = request.data.get("user_id")
        config = request.data.get("config")
        container = ContainerService.create_user_container(user_id, config)
        return Response(UserContainerSerializer(container).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="manage")
    def manage_container(self, request, pk=None):
        """管理容器（启动/停止/重启）"""
        action = request.data.get("action")
        result = ContainerService.manage_container(pk, action)
        return Response(result)

    @action(detail=True, methods=["get"], url_path="status")
    def get_container_status(self, request, pk=None):
        """查询容器实时状态"""
        status_info = ContainerService.get_container_status(pk)
        return Response(status_info)

    @action(detail=True, methods=["post"], url_path="update-resources")
    def update_container_resources(self, request, pk=None):
        """更新容器资源配置"""
        resource_config = request.data.get("resource_config")
        if not resource_config:
            return Response({"error": "缺少resource_config参数"}, status=status.HTTP_400_BAD_REQUEST)
        success = ContainerService.update_container_resources(pk, resource_config)
        return Response({"success": success})

    @action(detail=True, methods=["post"], url_path="destroy")
    def destroy_container(self, request, pk=None):
        """销毁容器"""
        success = ContainerService.destroy_user_container(pk)
        return Response({"success": success}, status=status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST)