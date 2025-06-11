# mission/templates/processor.py
import os
import logging
import jinja2
from django.conf import settings


logger = logging.getLogger(__name__)

# 注册处理函数
PROCESS_FUNCTIONS = {}

def register_processor(func_id):
    """函数装饰器，用于注册处理函数"""
    def decorator(func):
        PROCESS_FUNCTIONS[func_id] = func
        return func
    return decorator

def process_industry_template(industry, template_data, facility_params, scene):
    """
    根据行业和模拟器生成配置文件
    
    Args:
        industry: 行业对象
        template_data: 模板数据
        facility_params: 设施参数
        scene: 场景对象
    
    Returns:
        str: 配置文件内容
    """
    try:
        from resource.models import Simulator
        
        # 获取行业对应的模拟器
        simulators = Simulator.objects.filter(industry=industry)
        
        if not simulators.exists():
            logger.warning(f"No simulator found for industry {industry.industry_name}")
            return
        
        simulator = simulators.first()
        
        # 获取处理函数
        process_function_id = simulator.process_function_id
        
        if process_function_id not in PROCESS_FUNCTIONS:
            logger.error(f"Process function {process_function_id} not found")
            return ""
        
        # 处理数据
        processor = PROCESS_FUNCTIONS[process_function_id]
        processed_data = processor(template_data, facility_params)
        
        # 渲染模板
        config_files = render_templates(simulator, processed_data)
        
        # 保存配置文件
        save_configuration(scene, industry, config_files)
        
        return config_files
    
    except Exception as e:
        logger.error(f"Error generating industry template: {str(e)}")
        raise

def render_templates(simulator, processed_data):
    """
    渲染模板
    
    Args:
        simulator: 模拟器对象
        processed_data: 处理后的数据
    
    Returns:
        str: 渲染后的配置文件
    """
    # 加载Jinja2模板
    template_path = simulator.template_path
    template_dir = os.path.join(settings.BASE_DIR, 'templates')
    
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        autoescape=jinja2.select_autoescape(['html', 'xml'])
    )
    
    # 渲染模板
    template = env.get_template(template_path)
    rendered_content = template.render(**processed_data)
    
    # 根据模拟器类型添加不同的配置文件
    config_files = ""
    process_function_id = simulator.process_function_id
    
    if process_function_id == 'opendss_process':
        config_files += "/* Master File */\n"
        config_files += rendered_content
    
    elif process_function_id == 'omnet_process':
        # 生成ini文件
        config_files += "/* INI File */\n"
        config_files += rendered_content
        
        # 生成ned文件
        ned_template = env.get_template('omnet/ned_template.j2')
        ned_content = ned_template.render(**processed_data)
        config_files += "\n\n/* NED File */\n"
        config_files += ned_content
    
    elif process_function_id == 'fed_process':
        config_files += "/* FED File */\n"
        config_files += rendered_content
    
    return config_files

def save_configuration(scene, industry, config_files):
    """
    保存配置文件
    
    Args:
        scene: 场景对象
        industry: 行业对象
        config_files: 配置文件内容
    """
    # 更新或创建配置记录
    configuration, created = scene.configurations.get_or_create()
    
    # 将配置文件存储到合适的字段
    config_field = f'industry_{industry.industry_id}_simulator_config'
    setattr(configuration, config_field, config_files)
    configuration.save()
# mission/templates/template_manager.py
import logging

logger = logging.getLogger(__name__)

# 注册处理函数
PROCESS_FUNCTIONS = {}

def register_processor(func_id):
    """函数装饰器，用于注册处理函数"""
    def decorator(func):
        PROCESS_FUNCTIONS[func_id] = func
        return func
    return decorator

@register_processor('opendss_process')
def process_opendss(template_data, facility_params):
    """处理OpenDSS模拟器的数据"""
    processed_data = {
        'buses': [],
        'lines': [],
        'transformers': [],
        'generators': [],
        'loads': []
    }
    
    # 处理节点
    _process_opendss_nodes(template_data, facility_params, processed_data)
    
    # 处理边
    _process_opendss_edges(template_data, facility_params, processed_data)
    
    return processed_data

def _process_opendss_nodes(template_data, facility_params, processed_data):
    """处理OpenDSS节点"""
    for node in template_data.get('nodes', []):
        node_id = node.get('id')
        node_type = node.get('type')
        
        if node_type == 'bus':
            # 添加母线
            bus_data = {
                'name': node_id,
                'kv': facility_params.get(node_id, {}).get('kv', 138.0)
            }
            processed_data['buses'].append(bus_data)
        elif node_type == 'generator':
            # 添加发电机
            gen_data = {
                'name': node_id,
                'bus': node.get('bus'),
                'kw': facility_params.get(node_id, {}).get('kw', 100.0),
                'kvar': facility_params.get(node_id, {}).get('kvar', 50.0)
            }
            processed_data['generators'].append(gen_data)
        elif node_type == 'load':
            # 添加负载
            load_data = {
                'name': node_id,
                'bus': node.get('bus'),
                'kw': facility_params.get(node_id, {}).get('kw', 50.0),
                'kvar': facility_params.get(node_id, {}).get('kvar', 20.0)
            }
            processed_data['loads'].append(load_data)

def _process_opendss_edges(template_data, facility_params, processed_data):
    """处理OpenDSS边"""
    for edge in template_data.get('edges', []):
        edge_id = edge.get('id')
        edge_type = edge.get('type')
        source = edge.get('source')
        target = edge.get('target')
        
        if edge_type == 'line':
            # 添加线路
            line_data = {
                'name': edge_id,
                'bus1': source,
                'bus2': target,
                'length': facility_params.get(edge_id, {}).get('length', 1.0),
                'r1': facility_params.get(edge_id, {}).get('r1', 0.1),
                'x1': facility_params.get(edge_id, {}).get('x1', 0.1)
            }
            processed_data['lines'].append(line_data)
        elif edge_type == 'transformer':
            # 添加变压器
            xfmr_data = {
                'name': edge_id,
                'buses': [source, target],
                'kvs': [
                    facility_params.get(source, {}).get('kv', 138.0),
                    facility_params.get(target, {}).get('kv', 13.8)
                ],
                'kva': facility_params.get(edge_id, {}).get('kva', 1000.0)
            }
            processed_data['transformers'].append(xfmr_data)

@register_processor('omnet_process')
def process_omnet(template_data, facility_params):
    """处理OMNeT++模拟器的数据"""
    processed_data = {
        'nodes': [],
        'connections': [],
        'parameters': {}
    }
    
    # 处理节点
    for node in template_data.get('nodes', []):
        node_id = node.get('id')
        node_type = node.get('type')
        
        node_data = {
            'name': node_id,
            'type': node_type,
            'display': node.get('display', {}),
            'params': facility_params.get(node_id, {})
        }
        processed_data['nodes'].append(node_data)
    
    # 处理连接
    for edge in template_data.get('edges', []):
        edge_id = edge.get('id')
        source = edge.get('source')
        target = edge.get('target')
        
        connection_data = {
            'id': edge_id,
            'source': source,
            'target': target,
            'params': facility_params.get(edge_id, {})
        }
        processed_data['connections'].append(connection_data)
    
    # 全局参数
    processed_data['parameters'] = {
        'sim_time_limit': facility_params.get('global', {}).get('sim_time_limit', '1000s'),
        'network': facility_params.get('global', {}).get('network', 'GasNetwork')
    }
    
    return processed_data

@register_processor('fed_process')
def process_federation(template_data, facility_params):
    """处理联邦仿真的数据"""
    processed_data = {
        'federation_name': facility_params.get('global', {}).get('federation_name', 'EnergySystem'),
        'objects': [],
        'interactions': []
    }
    
    # 处理对象
    for node in template_data.get('nodes', []):
        node_id = node.get('id')
        node_type = node.get('type')
        
        object_data = {
            'name': node_id,
            'type': node_type,
            'attributes': facility_params.get(node_id, {}).get('attributes', [])
        }
        processed_data['objects'].append(object_data)
    
    # 处理交互
    for edge in template_data.get('edges', []):
        edge_id = edge.get('id')
        edge_type = edge.get('type')
        
        interaction_data = {
            'name': edge_id,
            'type': edge_type,
            'parameters': facility_params.get(edge_id, {}).get('parameters', [])
        }
        processed_data['interactions'].append(interaction_data)
    
    return processed_data