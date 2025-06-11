from django.test import TestCase
from django.contrib.auth import get_user_model
from ..userdb.models import UserContainer
from .services import ContainerService

User = get_user_model()

class ContainerManagementTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com")

    def test_create_container(self):
        """测试容器创建"""
        config = {"cpu_limit": "1000m", "memory_limit": "2Gi"}
        container = ContainerService.create_user_container(str(self.user.id), config)
        self.assertIsInstance(container, UserContainer)
        self.assertEqual(container.user, self.user)

# Create your tests here.
