from django.utils import timezone
from rest_framework import exceptions
from userdb.models import Token

class TokenValidator:
    @staticmethod
    def validate_token(token_key, required_scope=None):
        """验证Token有效性、过期时间、吊销状态和权限范围"""
        try:
            token = Token.objects.get(key=token_key)
            
            # 检查Token是否被吊销
            if token.is_revoked:
                raise exceptions.AuthenticationFailed('Token has been revoked')
                
            # 检查Token是否过期
            if token.expires_at and token.expires_at < timezone.now():
                raise exceptions.AuthenticationFailed('Token has expired')
                
            # 检查权限范围
            if required_scope and required_scope not in token.scope.split(','):
                raise exceptions.AuthenticationFailed('Token does not have required scope')
                
            return token.user
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')