# 导入 Celery 实例，确保 Django 启动时加载
from .celery import app as celery_app

__all__ = ('celery_app',)

# 添加PyMySQL兼容声明
import pymysql
pymysql.install_as_MySQLdb()