import json

def merge_split_json(device_params_json, topology_json):
    """
    将拆分后的设备参数JSON和拓扑JSON合并成完整的原始JSON格式
    
    Args:
        device_params_json: 设备参数JSON数据
        topology_json: 拓扑连接JSON数据
    
    Returns:
        dict: 合并后的完整JSON
    """
    
    # 如果输入是字符串，则解析为字典
    if isinstance(device_params_json, str):
        device_params = json.loads(device_params_json)
    else:
        device_params = device_params_json
        
    if isinstance(topology_json, str):
        topology = json.loads(topology_json)
    else:
        topology = topology_json
    
    # 构建完整的JSON结构
    complete_json = {}
    
    # 1. 构建omnetpp部分
    omnetpp_section = {}
    
    # 从拓扑JSON中获取网络配置
    omnetpp_section.update(topology['network_config'])
    
    # 从设备参数中获取压缩机参数
    compressor_device = next((device for device in device_params['devices'] 
                             if device['device_type'] == 'compressor'), None)
    
    if compressor_device:
        omnetpp_section['compressor_params'] = compressor_device['parameters']
        omnetpp_section['compressor_desc'] = compressor_device['parameter_descriptions']
    
    complete_json['omnetpp'] = omnetpp_section
    
    # 2. 构建topology部分
    topology_section = {}
    
    # 构建submodules列表
    submodules = []
    for node in topology['nodes']:
        submodule = {
            "name": node['name'],
            "type": node['type'],
            "position": node['position']
        }
        submodules.append(submodule)
    
    topology_section['submodules'] = submodules
    
    # 构建connections列表（移除添加的connection_type）
    connections = []
    for conn in topology['connections']:
        connection = {
            "source": conn['source'],
            "target": conn['target']
        }
        connections.append(connection)
    
    topology_section['connections'] = connections
    
    complete_json['topology'] = topology_section
    
    return complete_json

def split_omnet_json(original_json):
    """
    将原始JSON拆分为设备参数JSON和拓扑JSON
    
    Args:
        original_json: 原始完整JSON数据
        
    Returns:
        tuple: (device_params_json, topology_json)
    """
    
    if isinstance(original_json, str):
        data = json.loads(original_json)
    else:
        data = original_json
    
    # 构建设备参数JSON
    device_params = {"devices": []}
    
    # 添加压缩机参数
    if 'omnetpp' in data and 'compressor_params' in data['omnetpp']:
        compressor_device = {
            "device_type": "compressor",
            "device_name": "default_compressor",
            "parameters": data['omnetpp']['compressor_params'],
            "parameter_descriptions": data['omnetpp'].get('compressor_desc', {})
        }
        device_params['devices'].append(compressor_device)
    
    # 按设备类型分组节点
    if 'topology' in data and 'submodules' in data['topology']:
        device_types = {}
        for submodule in data['topology']['submodules']:
            device_type = submodule['type']
            if device_type not in device_types:
                device_types[device_type] = []
            device_types[device_type].append({
                "name": submodule['name'],
                "position": submodule['position']
            })
        
        # 为每种设备类型创建条目
        for device_type, instances in device_types.items():
            if device_type != 'Compressor' or len(instances) > 0:  # 避免与压缩机参数重复
                device_entry = {
                    "device_type": device_type,
                    "instances": instances
                }
                device_params['devices'].append(device_entry)
    
    # 构建拓扑JSON
    topology_json = {}
    
    # 网络配置
    if 'omnetpp' in data:
        network_config = {}
        for key, value in data['omnetpp'].items():
            if key not in ['compressor_params', 'compressor_desc']:
                network_config[key] = value
        topology_json['network_config'] = network_config
    
    # 节点信息
    if 'topology' in data and 'submodules' in data['topology']:
        topology_json['nodes'] = data['topology']['submodules']
    
    # 连接关系（添加连接类型）
    if 'topology' in data and 'connections' in data['topology']:
        connections = []
        for conn in data['topology']['connections']:
            connection = conn.copy()
            # 根据源节点类型推断连接类型
            source_type = None
            if 'nodes' in topology_json:
                for node in topology_json['nodes']:
                    if node['name'] == conn['source']:
                        source_type = node['type']
                        break
            
            if source_type == 'Compressor':
                connection['connection_type'] = 'compression'
            else:
                connection['connection_type'] = 'gas_flow'
            
            connections.append(connection)
        
        topology_json['connections'] = connections
    
    return device_params, topology_json

# # 使用示例
# if __name__ == "__main__":
#     # 示例：加载拆分后的JSON文件并合并
#     try:
#         import os
#         omnet_data = os.path.join(os.path.dirname(__file__), '..', 'omnet.json')
#         with open(omnet_data, 'r', encoding='utf-8') as f:
#             original_json = json.load(f)
#         device_params_json, topology_json = split_omnet_json(original_json)

#         with open('device_params.json', 'w', encoding='utf-8') as f:
#             json.dump(device_params_json, f, indent=2, ensure_ascii=False)
#             # device_params = json.load(f)
        
#         with open('topology.json', 'w', encoding='utf-8') as f:
#             json.dump(topology_json, f, indent=2, ensure_ascii=False)
#             # topology = json.load(f)
        
#         # 合并JSON
#         merged_json = merge_split_json(device_params_json, topology_json)
        
#         # 保存合并后的JSON
#         with open('merged_omnet.json', 'w', encoding='utf-8') as f:
#             json.dump(merged_json, f, indent=2, ensure_ascii=False)
        
#         print("JSON合并完成，已保存到 merged_omnet.json")
        
#     except FileNotFoundError:
#         print("请确保device_params.json和topology.json文件存在")
#     except Exception as e:
#         print(f"处理过程中出现错误: {e}")