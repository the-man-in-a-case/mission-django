#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
拓扑文件生成器
使用JSON数据和Jinja2模板生成网络拓扑配置文件
"""

import json
import os
from jinja2 import Environment, FileSystemLoader

class TopologyGenerator:
    def __init__(self, data_file=None):
        """
        初始化生成器
        
        Args:
            data_file: JSON数据文件路径
        """
        if not data_file:
            raise ValueError("必须提供data_file参数")
        with open(data_file, 'r', encoding='utf-8') as f:
            self.data = json.load(f)

    def generate_config(self, template_file, output_file):
        """
        从模板生成配置文件
        
        Args:
            template_file: 模板文件路径
            output_file: 输出文件路径
        """
        template_dir = os.path.dirname(template_file)
        template_name = os.path.basename(template_file)
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template(template_name)
        rendered = template.render(self.data)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(rendered)
        print(f"已生成文件: {output_file}")

def main():
    # 定义文件路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = os.path.join(base_dir, 'topology_data.json')
    ini_template = os.path.join(base_dir, 'topology.ini.j2')
    ned_template = os.path.join(base_dir, 'topology.ned.j2')
    ini_output = os.path.join(base_dir, 'new_topology.ini（参数配置）')
    ned_output = os.path.join(base_dir, 'new_topology.ned （拓扑结构）')

    # 初始化生成器
    generator = TopologyGenerator(data_file=data_file)

    # 生成INI配置文件
    generator.generate_config(ini_template, ini_output)

    # 生成NED拓扑文件
    generator.generate_config(ned_template, ned_output)

    print("生成完成！")

if __name__ == "__main__":
    main()