from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from rest_framework.authtoken.models import Token
from django.utils import timezone

class TokenAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # 排除不需要认证的路径
        excluded_paths = ['/api/auth/login/', '/admin/', '/prometheus/']
        if any(request.path.startswith(path) for path in excluded_paths):
            return

        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Token '):
            return JsonResponse({
                'error': 'Authentication credentials were not provided'
            }, status=401)

        token_key = auth_header.split(' ')[1]
        try:
            token = Token.objects.get(key=token_key)
            # 检查token是否过期
            if token.expires_at and token.expires_at < timezone.now():
                return JsonResponse({'error': 'Token has expired'}, status=401)
            # 检查token是否被吊销
            if token.is_revoked:
                return JsonResponse({'error': 'Token has been revoked'}, status=401)
            # 更新最后使用时间
            token.last_used = timezone.now()
            token.save()
            # 将用户添加到请求对象
            request.user = token.user
        except Token.DoesNotExist:
            return JsonResponse({'error': 'Invalid token'}, status=401)