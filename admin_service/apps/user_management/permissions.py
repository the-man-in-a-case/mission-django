from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """管理员权限或只读权限：安全方法（GET/HEAD/OPTIONS）允许认证用户，非安全方法仅管理员"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated  # 认证用户可读取
        return request.user.is_authenticated and request.user.is_staff  # 仅管理员可写

class IsOwnerOrAdmin(permissions.BasePermission):
    """所有者或管理员权限：仅对象所有者或管理员可操作"""
    def has_object_permission(self, request, view, obj):
        return obj == request.user or request.user.is_staff  # obj 需为 User 实例