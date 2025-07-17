from django.utils import timezone
from userdb.models import AlertRule, ContainerInstance
import logging
import requests 
from django.conf import settings  

logger = logging.getLogger(__name__)

class AlertManager:
    """警报管理器"""
    
    def check_alerts(self):
        """执行警报检查"""
        active_rules = AlertRule.objects.filter(is_active=True)
        for rule in active_rules:
            self._evaluate_rule(rule)
    
    def _evaluate_rule(self, rule):
        """评估单个警报规则"""
        try:
            instance = rule.container_instance
            condition_met = eval(rule.trigger_condition, {
                'instance': instance,
                'health_checks': instance.health_records.all()
            })
            
            if condition_met and not rule.triggered_at:
                self._trigger_alert(rule)
            elif not condition_met and rule.triggered_at:
                self._resolve_alert(rule)
                
        except Exception as e:
            logger.error(f"警报规则评估失败: {str(e)}")

    def _trigger_alert(self, rule):
        """触发警报并发送通知"""
        rule.triggered_at = timezone.now()
        rule.save()
        # 此处应集成通知系统
        logger.warning(f"触发警报: {rule.message}")

        # 新增: Webhook通知实现
        self._send_webhook_notification(rule)

    def _send_webhook_notification(self, rule: AlertRule):
        """通过Webhook发送告警通知"""
        if not settings.MONITORING_WEBHOOK_URL:
            logger.warning("未配置告警Webhook URL，无法发送通知")
            return

        try:
            payload = {
                'alert_id': rule.id,
                'level': rule.level,
                'message': rule.message,
                'trigger_condition': rule.trigger_condition,
                'triggered_at': rule.triggered_at.isoformat(),
                'container_instance': rule.container_instance.instance_id,
                'container_name': rule.container_instance.container.name
            }

            response = requests.post(
                settings.MONITORING_WEBHOOK_URL,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.info(f"告警Webhook通知发送成功: {rule.id}")
        except Exception as e:
            logger.error(f"告警Webhook通知发送失败: {str(e)}")

    def _resolve_alert(self, rule):
        """解除警报"""
        rule.triggered_at = None
        rule.save()
        logger.info(f"警报解除: {rule.message}")