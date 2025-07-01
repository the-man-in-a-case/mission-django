# 确保Celery应用在Django启动时被加载
from .celery import app as celery_app

__all__ = ('celery_app',)

# 添加PyMySQL兼容声明
import pymysql
pymysql.install_as_MySQLdb()