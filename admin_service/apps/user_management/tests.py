from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.authtoken.models import Token
from .models import User, UserActivity

class UserManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username='admin', email='admin@example.com', password='admin123'
        )
        self.normal_user = User.objects.create_user(
            username='testuser', email='test@example.com', password='test123'
        )
        self.admin_token = Token.objects.get(user=self.admin_user).key
        self.normal_token = Token.objects.get(user=self.normal_user).key

    def test_user_create(self):
        """测试用户创建接口（需管理员权限）"""
        url = reverse('users-list')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'new123',
            'confirm_password': 'new123',
            'permission_level': 'basic'
        }
        response = self.client.post(url, data, HTTP_AUTHORIZATION=f'Token {self.admin_token}')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.filter(username='newuser').count(), 1)

    def test_user_login(self):
        """测试用户登录接口"""
        url = reverse('auth-login')
        data = {'username': 'testuser', 'password': 'test123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.data['data'])

    def test_container_management(self):
        """测试容器管理接口（启动/停止）"""
        url = reverse('users-manage_container', kwargs={'pk': self.normal_user.id})
        data = {'action': 'start'}
        response = self.client.post(
            url, data, HTTP_AUTHORIZATION=f'Token {self.admin_token}'
        )
        self.assertEqual(response.status_code, 200)
        self.normal_user.refresh_from_db()
        self.assertEqual(self.normal_user.container_status, 'running')  # 假设容器启动后状态为 'running'