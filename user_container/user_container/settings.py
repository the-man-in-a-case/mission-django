"""
Django settings for user_container project.

Generated by 'django-admin startproject' using Django 4.2.7.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-_9qtl4tbt4)s8)_7+5$055_9lr8!b5i_k74wxyepnfw19vbow*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

APPEND_SLASH = False
# Application definition

INSTALLED_APPS = [
    'jazzmin',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    #第三方
    'rest_framework',
    'rest_framework.authtoken',  # 添加DRF Token认证应用

    #新增app
    # 'apps.gateway_client',
    'apps.business_flow',
    'apps.resourcedb',
    'django_celery_results',  # Add this line
]

# 添加REST Framework配置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',  # 启用Token认证
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',  # 全局要求认证
    )
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.route_management.middleware.RequestMetricsMiddleware', 
]

ROOT_URLCONF = 'user_container.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'user_container.wsgi.application'

JAZZMIN_SETTINGS = {
    "site_title": "城市级联系统后台",  # 登录页和标签栏标题
    "site_header": "城市级联系统",  # 后台顶部标题
    "site_brand": "信工所",  # 左上角品牌名称
    # "site_logo": 'xgs_logo_.png',  # 自定义LOGO（路径需配置静态文件）
    "welcome_sign": "欢迎使用 城市级联系统 后台",  # 仪表盘欢迎语
    "theme": "default",  # 可选主题："default", "darkly", "cyborg", "slate"等
    "dark_mode_theme": "darkly",  # 深色模式主题
    "show_ui_builder": True,  # 启用可视化布局编辑器（需安装额外插件）
    "order_with_respect_to": ["auth", "demo_app", "demo_app2"],  # 按应用排序菜单
    "hide_models": ["auth.Group"],  # 隐藏特定模型（如默认的Group）
    "icons": {
        "auth": "fas fa-users-cog",  # 为应用添加图标（使用Font Awesome类）
        "auth.User": "fas fa-user",
        "app1.Model1": "fas fa-book",
    },
}

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

ADMIN_SERVICE_BASE_URL = ''

# Redis 配置
REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

# InfluxDB 配置
INFLUXDB_HOST = 'influxdb'
INFLUXDB_PORT = 8086
INFLUXDB_TOKEN = None
INFLUXDB_ORG = None
INFLUXDB_BUCKET = None
# RabbitMQ 配置
# RABBITMQ_HOST = '192.168.119.200'
# RABBITMQ_PORT = 30074
RABBITMQ_HOST = 'rabbitmq'
RABBITMQ_PORT = 5672
RABBITMQ_USERNAME = 'admin'
# RABBITMQ_PASSWORD = 'admin123'
RABBITMQ_PASSWORD = 'password'
QUEUE_NAME = 'calculation'
EXCHANGE_NAME = 'calculation'

# 新增：用户网关服务配置（根据实际环境填写URL）
USER_GATEWAY_URL = 'http://user-gateway:8000'  # 示例值，需替换为实际网关地址

# Celery配置


CELERY_BEAT_SCHEDULE = {
    'collect-exceptions': {
        'task': 'gateway_client.tasks.collect_exceptions_task',
        'schedule': 60.0,
    },
    'report-exceptions': {
        'task': 'gateway_client.tasks.report_exceptions_task',
        'schedule': 300.0,
    },
    'report-health-metrics': {
        'task': 'gateway_client.tasks.report_health_metrics_task',
        'schedule': 60.0,
    },
}

# 外部服务URL配置
USER_GATEWAY_URL = 'http://localhost:8000'
ROUTE_MANAGEMENT_URL = 'http://localhost:8000'
MONITORING_SERVICE_URL = 'http://localhost:8000'


# Celery 配置
CELERY_BROKER_URL = f"amqp://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}//"  # 使用 RabbitMQ 作为消息代理
CELERY_RESULT_BACKEND = "django-db"  # 使用 Django 数据库存储任务结果（需安装 django-celery-results）
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE  # 与 Django 时区保持一致
CELERY_TASK_TRACK_STARTED = True  # 跟踪任务启动状态
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# 默认队列、交换机和路由键等配置
CELERY_TASK_QUEUES = {
    'default': {
        'exchange': 'default',
        'routing_key': 'task.default',
    }
}
CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'task.default'

# 如果需要更细粒度地控制 Exchange 和 Queue 的属性
from kombu import Exchange, Queue
CELERY_TASK_QUEUES = (
    Queue('default', Exchange('default'), routing_key='default'),
)