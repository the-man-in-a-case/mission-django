# ... existing code ...
from .celery import app as celery_app

__all__ = ("celery_app",)
# 原有内容（可能为空或其他初始化代码）

# 添加PyMySQL兼容声明
import pymysql
pymysql.install_as_MySQLdb()