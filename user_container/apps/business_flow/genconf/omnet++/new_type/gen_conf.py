#!/usr/bin/env python3
"""
OMNeT++ Topology Generator using Jinja2 templates
生成topology.ini和topology.ned文件
"""

import json
import os
from jinja2 import Environment, FileSystemLoader, Template

def load_data(json_file):
    """加载JSON数据文件"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_files(data, template_dir='.', output_dir='.'):
    """
    使用Jinja2模板生成配置文件
    
    Args:
        data: 包含网络拓扑数据的字典
        template_dir: 模板文件目录
        output_dir: 输出文件目录
    """
    
    # 设置Jinja2环境
    env = Environment(
        loader=FileSystemLoader(template_dir),
        trim_blocks=True,
        lstrip_blocks=True
    )
    
    # 生成topology.ini文件
    ini_template = env.get_template('topology.ini.j2')
    ini_content = ini_template.render(data)
    
    ini_output_path = os.path.join(output_dir, 'topology.ini')
    with open(ini_output_path, 'w', encoding='utf-8') as f:
        f.write(ini_content)
    print(f"Generated: {ini_output_path}")
    
    # 生成topology.ned文件
    ned_template = env.get_template('topology.ned.j2')
    ned_content = ned_template.render(data)
    
    ned_output_path = os.path.join(output_dir, 'topology.ned')
    with open(ned_output_path, 'w', encoding='utf-8') as f:
        f.write(ned_content)
    print(f"Generated: {ned_output_path}")

def generate_from_strings(data, ini_template_str, ned_template_str):
    """
    直接从模板字符串生成文件（用于演示）
    
    Args:
        data: 包含网络拓扑数据的字典
        ini_template_str: INI模板字符串
        ned_template_str: NED模板字符串
    
    Returns:
        tuple: (ini_content, ned_content)
    """
    
    # 创建Jinja2模板对象
    ini_template = Template(ini_template_str, trim_blocks=True, lstrip_blocks=True)
    ned_template = Template(ned_template_str, trim_blocks=True, lstrip_blocks=True)
    
    # 渲染模板
    ini_content = ini_template.render(data)
    ned_content = ned_template.render(data)
    
    return ini_content, ned_content

def validate_data(data):
    """验证数据格式"""
    required_keys = ['network_name', 'nodes', 'edges', 'global_params']
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")
    
    # 验证nodes结构
    for i, node in enumerate(data['nodes']):
        node_required = ['id', 'type', 'display']
        for key in node_required:
            if key not in node:
                raise ValueError(f"Node {i} missing required key: {key}")
    
    # 验证edges结构
    for i, edge in enumerate(data['edges']):
        edge_required = ['from', 'to', 'pipe_type']
        for key in edge_required:
            if key not in edge:
                raise ValueError(f"Edge {i} missing required key: {key}")
    
    print("Data validation passed!")

def main():
    """主函数 - 演示如何使用"""
    
    # 示例数据文件路径
    json_file = 'topology_data.json'
    
    # 如果JSON文件不存在，创建示例数据
    if not os.path.exists(json_file):
        print(f"Creating sample data file: {json_file}")
        # 这里可以放置示例数据创建代码
        pass
    
    try:
        # 加载数据
        data = load_data(json_file)
        
        # 验证数据
        validate_data(data)
        
        # 生成文件
        generate_files(data)
        
        print("Files generated successfully!")
        
    except FileNotFoundError:
        print(f"Error: Data file {json_file} not found!")
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {json_file}: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    main()