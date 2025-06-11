from django.test import TestCase
from django.contrib.auth import get_user_model
from ..userdb.models import User, UserContainer, ContainerInstance
from .models import RouteRegistry, HealthCheckRecord

User = get_user_model()

class LoadBalancerTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.container = UserContainer.objects.create(user=self.user, container_name="test-container")
        self.instance = ContainerInstance.objects.create(
            container=self.container,
            instance_id="inst-1",
            pod_ip="10.0.0.1",
            port=8080,
            status='running',
            is_healthy=True
        )
        self.route = RouteRegistry.objects.create(
            user=self.user,
            container=self.container,
            route_path="/api/test"
        )

    def test_health_check_record(self):
        """测试健康检查记录创建"""
        record = HealthCheckRecord.objects.create(
            container_instance=self.instance,
            is_healthy=True,
            response_time=200.5,
            status_code=200,
            check_url=f"{self.instance.service_url}/health"
        )
        self.assertEqual(record.container_instance, self.instance)
        self.assertTrue(record.is_healthy)
