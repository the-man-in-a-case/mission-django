# 原硬编码配置改为从Django settings读取
from django.conf import settings
import pika
import json, time
import logging

logger = logging.getLogger(__name__)

# 从配置中获取RabbitMQ参数（修正变量名）
RABBITMQ_HOST = settings.RABBITMQ_HOST
RABBITMQ_PORT = settings.RABBITMQ_PORT
RABBITMQ_USERNAME = settings.RABBITMQ_USERNAME
RABBITMQ_PASSWORD = settings.RABBITMQ_PASSWORD
QUEUE_NAME = settings.QUEUE_NAME  # 修正：原 RABBITMQ_QUEUE_NAME 改为 QUEUE_NAME
EXCHANGE_NAME = settings.EXCHANGE_NAME  # 修正：原 RABBITMQ_EXCHANGE_NAME 改为 EXCHANGE_NAME

def send_to_rabbitmq(project_id, target_data):
    """发送目标数据到RabbitMQ队列（优化版）"""
    try:
        # 连接参数配置
        credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=RABBITMQ_HOST,
                port=RABBITMQ_PORT,
                credentials=credentials,
                heartbeat=600  # 增加心跳防止连接断开
            )
        )
        channel = connection.channel()

        # 声明持久化交换机和队列（确保服务重启后消息不丢失）
        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type='direct', durable=True)
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME, routing_key=QUEUE_NAME)

        # 构造业务相关的消息体（使用project_id和target_data）
        message = {
            'project_id': project_id,
            'node': target_data['node'],
            'timestamp': target_data['time']  # 添加时间戳
        }

        print(f"发送的消息内容: {json.dumps(message)}")  # 打印消息内容

        # 发送持久化消息
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # 消息持久化
                content_type='application/json'
            )
        )
        logger.info(f"已发送项目 {project_id} 的目标数据到RabbitMQ，数据量：{len(json.dumps(message))} bytes")

    except pika.exceptions.AMQPConnectionError as e:
        logger.error(f"RabbitMQ连接失败: {str(e)}")
        raise  # 重新抛出异常以便上层处理
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}", exc_info=True)
        raise
    finally:
        # 确保连接关闭
        if 'connection' in locals() and connection.is_open:
            connection.close()
            logger.debug("RabbitMQ连接已关闭")