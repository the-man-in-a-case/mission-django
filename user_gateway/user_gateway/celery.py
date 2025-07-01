import os
from celery import Celery

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'user_gateway.settings')

# 初始化Celery应用
app = Celery('user_gateway')

# 从Django配置中加载Celery配置（前缀为CELERY_）
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现所有Django应用中的tasks.py文件
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')