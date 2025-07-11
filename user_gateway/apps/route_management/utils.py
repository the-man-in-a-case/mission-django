from django.utils import timezone
from rest_framework import exceptions
from userdb.models import Token

class TokenValidator:
    @staticmethod
    def validate_token(token_key):
        """验证Token有效性和过期时间"""
        try:
            token = Token.objects.get(key=token_key)
            # 检查Token是否过期
            if token.expires_at and token.expires_at < timezone.now():
                raise exceptions.AuthenticationFailed('Token has expired')
            return token.user
        except Token.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')