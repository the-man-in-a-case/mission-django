from django.test import TestCase
from django.urls import reverse
from .models import ServiceInstance
from unittest.mock import patch

class GatewayClientTests(TestCase):
    def setUp(self):
        self.service_instance = ServiceInstance.objects.create(
            service_id="user123-business_flow",
            service_type="business_flow",
            host="10.0.0.1",
            port=8000
        )

    @patch('apps.gateway_client.registry_client.GatewayRegistryClient.register')
    def test_register_service(self, mock_register):
        mock_register.return_value = {
            'status': 'success',
            'service_id': 'user123-business_flow'
        }
        response = self.client.post(
            reverse('register_service'),
            {'service_type': 'business_flow'},
            HTTP_HOST='10.0.0.1:8000'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ServiceInstance.objects.filter(
            service_id='user123-business_flow'
        ).exists())

    @patch('apps.gateway_client.registry_client.GatewayRegistryClient.report_health')
    def test_report_health(self, mock_report):
        mock_report.return_value = {'status': 'success'}
        response = self.client.get(
            reverse('report_health'),
            {'service_id': 'user123-business_flow', 'is_healthy': 'true'}
        )
        self.assertEqual(response.status_code, 200)
        self.service_instance.refresh_from_db()
        self.assertTrue(self.service_instance.is_healthy)
