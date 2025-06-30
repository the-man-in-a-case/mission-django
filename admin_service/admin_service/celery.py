import os
from celery import Celery

# 设置 Django 环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'admin_service.settings')

# 初始化 Celery 应用
app = Celery('admin_service')

# 从 Django 配置中加载 Celery 配置（前缀为 CELERY_）
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现所有 Django 应用中的 tasks.py 文件
app.autodiscover_tasks()