import json
import os
import re

# Get the absolute path to the current script directory
script_dir = os.path.dirname(os.path.abspath(__file__))

# Construct absolute path to the source JSON files
source_json_path = os.path.join(script_dir, '..', '..', 'test_data', 'opendss.json')
master_json_path = os.path.join(script_dir, '..', '..', 'test_data', 'opendss_master_file.json')

# Normalize the paths to handle any redundant components
source_json_path = os.path.normpath(source_json_path)
master_json_path = os.path.normpath(master_json_path)

# Output JSON path (in current script directory)
output_json_path = os.path.join(script_dir, 'data.json')

# Verify source files exist before opening
if not os.path.exists(source_json_path):
    raise FileNotFoundError(f"Source JSON file not found at: {source_json_path}")
if not os.path.exists(master_json_path):
    raise FileNotFoundError(f"Master JSON file not found at: {master_json_path}")

# Read source data
with open(source_json_path, 'r') as f:
    source_data = json.load(f)

# Read master file data
with open(master_json_path, 'r') as f:
    master_data = json.load(f)

# 提取总线ID的辅助函数
def extract_bus_id(bus_name):
    match = re.search(r'^\d+', bus_name)
    return match.group() if match else bus_name

# 收集所有唯一的节点(bus)
node_set = set()

# 从线路中收集节点
lines = source_data.get('lines', {}).get('138kV_lines', {}).get('lines', [])
for line in lines:
    node_set.add(line['bus1'])
    node_set.add(line['bus2'])

# 从发电机中收集节点
for generator in source_data.get('generators', []):
    if 'bus' in generator:
        node_set.add(generator['bus'])

# 从负载中收集节点
loads = source_data.get('loads', {}).get('138kV_loads', {}).get('loads', [])
for load in loads:
    node_set.add(load['bus'])

# 构建nodedata
nodedata = []
for bus_name in node_set:
    node_id = extract_bus_id(bus_name)
    # 提取节点名称（去掉数字前缀和下划线）
    node_name = re.sub(r'^\d+_', '', bus_name)
    nodedata.append({
        'id': node_id,
        'name': node_name,
        'type': 'bus',  # 默认类型为bus
        'position': '',  # 位置信息暂未提供，留空
        'properties': {}
    })

# 构建edgedata
edgedata = []
for line in lines:
    edge_id = line['name']
    # 提取边类型（使用下划线分割的最后部分）
    edge_type = edge_id.split('_')[-1] if '_' in edge_id else 'line'
    edgedata.append({
        'from': extract_bus_id(line['bus1']),
        'to': extract_bus_id(line['bus2']),
        'edgetype': edge_type,
        'properties': {
            'r1': line['r1'],
            'x1': line['x1'],
            'r0': line['r0'],
            'x0': line['x0'],
            'c1': line['c1'],
            'c0': line['c0']
        }
    })

# 构建global_params
global_params = {
    'voltage_level': source_data.get('voltage_level', '138.0'),
    'circuit_name': master_data.get('circuit_name', ''),
    'default_base_frequency': master_data.get('default_base_frequency', ''),
    'voltage_bases': master_data.get('voltage_bases', ''),
    'algorithm': master_data.get('algorithm', ''),
    'ignore_gen_q_limits': master_data.get('ignore_gen_q_limits', ''),
    **master_data.get('circuit_params', {})
}

# 转换并合并为模板所需的新结构
template_data = {
    'global_params': global_params,
    'nodedata': nodedata,
    'edgedata': edgedata
}

# 保存为JSON文件
with open(output_json_path, 'w') as f:
    json.dump(template_data, f, indent=4)

print(f'JSON数据文件已生成: {os.path.abspath(output_json_path)}')