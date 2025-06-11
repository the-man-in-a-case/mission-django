from django.db import models
from django.core.exceptions import ValidationError
from resourcedb.models import Map, Layer

class ResourceImportJob(models.Model):
    """资源导入任务模型（记录导入操作的状态和日志）"""
    
    IMPORT_TYPE_CHOICES = [
        ('map', 'Map 级联导入'),
        ('layer', 'Layer 级联导入'),
    ]
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('running', '执行中'),
        ('success', '成功'),
        ('failed', '失败'),
    ]

    import_type = models.CharField(max_length=10, choices=IMPORT_TYPE_CHOICES, help_text='导入类型')
    target_id = models.PositiveIntegerField(help_text='目标 Map/Layer ID')  # 关联 Map 或 Layer 的 ID
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', help_text='任务状态')
    log = models.TextField(blank=True, help_text='导入日志')
    created_at = models.DateTimeField(auto_now_add=True, help_text='任务创建时间')
    updated_at = models.DateTimeField(auto_now=True, help_text='任务更新时间')
    api_data = models.JSONField(null=True, blank=True, help_text='外部API输入的原始数据')  # 新增字段

    class Meta:
        db_table = 'ResourceImportJob'
        verbose_name = '资源导入任务'
        verbose_name_plural = '资源导入任务'

    def clean(self):
        """校验目标 ID 是否存在"""
        if self.import_type == 'map' and not Map.objects.filter(id=self.target_id).exists():
            raise ValidationError({'target_id': '目标 Map 不存在'})
        if self.import_type == 'layer' and not Layer.objects.filter(id=self.target_id).exists():
            raise ValidationError({'target_id': '目标 Layer 不存在'})

    def __str__(self):
        return f"ImportJob-{self.id} ({self.get_import_type_display()})"
