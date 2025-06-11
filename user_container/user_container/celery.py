import os
from celery import Celery

# 设置 Django 默认配置
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "user_container.settings")

app = Celery("user_container")

# 从 Django settings 中加载配置（以 CELERY_ 开头的配置项）
app.config_from_object("django.conf:settings", namespace="CELERY")

# 自动发现所有 app 下的 tasks.py
app.autodiscover_tasks()