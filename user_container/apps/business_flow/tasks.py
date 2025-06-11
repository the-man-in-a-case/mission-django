import queue
from celery import shared_task
from django.core.exceptions import ObjectDoesNotExist
from . import utils
from ..resourcedb.models import Project
# from ..k8s_client import K8sDeployer  # 假设已封装k8s客户端
import networkx as nx
import json
from .rabbitmq import send_to_rabbitmq
import logging

logger = logging.getLogger(__name__)

@shared_task
def generate_topology_and_config(project_id):
    """生成拓扑图和模拟器配置"""
    try:
        project = Project.objects.get(id=project_id)
        # 构建networkx图
        graph = utils.build_networkx_graph(project.layers.all())
        # 生成topo json
        topo_json = utils.generate_topo_json(graph)
        # 生成模拟器配置（假设每个layer有对应的jinja2模板）
        for layer in project.layers.all():
            config_content = utils.render_simulation_config(layer, graph)
            # 保存到Configuration表（假设Configuration需要扩展）
            layer.configuration_set.create(content=config_content)  # 需修改Configuration模型添加content字段
        
        # 更新项目状态
        project.status = 'initial'
        project.save()
        
        # 单点模式自动触发部署
        if 'single_point' in project.task_modes:
            deploy_single_task_environment.delay(project_id)
            
    except ObjectDoesNotExist:
        pass

@shared_task
def deploy_single_task_environment(project_id):
    """部署单点任务环境（k8s）"""
    project = Project.objects.get(id=project_id)
    # deployer = K8sDeployer()
    # pod_id = deployer.deploy_simulation_environment(project)  # 调用k8s API部署
    project.pod_id = pod_id
    project.status = 'success'
    project.save()

@shared_task
def calculate_brute_force_combinations(project_id, area_json):
    """计算暴力计算组合"""
    project = Project.objects.get(id=project_id)
    graph = utils.build_networkx_graph(project.layers.all())
    area_graph = utils.build_networkx_graph_from_area(area_json)
    combinations = utils.calculate_node_path_combinations(graph, area_graph)
    
    # 分发任务到celery worker
    for combo in combinations:
        tasks.execute_brute_force_task.delay(project_id, combo)

@shared_task(queue='default')
def send_target_to_rabbitmq(project_id, target_data):
    """Celery任务：将目标数据发送到RabbitMQ"""
    try:
        print(f"任务 {send_target_to_rabbitmq.request.id} 开始：项目 {project_id} 目标数据发送{target_data}")
        # 直接调用优化后的rabbitmq发送函数
        send_to_rabbitmq(project_id, target_data)
        logger.info(f"任务 {send_target_to_rabbitmq.request.id} 完成：项目 {project_id} 目标数据已发送")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"任务 {send_target_to_rabbitmq.request.id} 失败：{str(e)}")
        raise  # 保持异常以便Celery重试机制生效