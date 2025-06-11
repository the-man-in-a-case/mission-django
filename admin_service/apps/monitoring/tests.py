from django.test import TestCase
from rest_framework.test import APIClient
from apps.userdb.models import User, UserContainer
from .models import AlertRule

class MonitoringAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com')
        self.container = UserContainer.objects.create(
            user=self.user,
            container_name='test-container',
            cpu_limit='1000m',
            memory_limit='2Gi'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_container_metrics_api(self):
        response = self.client.get(f'/api/monitoring/containers/{self.container.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('cpu_limit', response.data)

    def test_alert_rule_creation(self):
        rule_count = AlertRule.objects.count()
        self.client.post('/api/monitoring/alerts/rules/', {
            'rule_type': 'container_cpu',
            'threshold': 90,
            'container': str(self.container.id)
        })
        self.assertEqual(AlertRule.objects.count(), rule_count + 1)
