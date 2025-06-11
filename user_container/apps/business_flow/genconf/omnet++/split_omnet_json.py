import json
import os

def split_omnet_json(omnet_path, nodes_output_path, topology_output_path):
    # 检查输入文件是否存在
    if not os.path.exists(omnet_path):
        raise FileNotFoundError(f"错误：文件 {omnet_path} 不存在")

    # 读取原始 JSON 数据
    with open(omnet_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 提取拓扑结构（submodules 和 connections）
    topology_structure = {
        "submodules": data["topology"]["submodules"],
        "connections": data["topology"]["connections"]
    }
    
    # 提取节点信息（nodes）
    nodes_info = {"nodes": data["topology"]["nodes"]}

    # 写入拓扑结构文件
    with open(topology_output_path, 'w', encoding='utf-8') as f:
        json.dump(topology_structure, f, indent=2, ensure_ascii=False)
    
    # 写入节点信息文件
    with open(nodes_output_path, 'w', encoding='utf-8') as f:
        json.dump(nodes_info, f, indent=2, ensure_ascii=False)

    print(f"拆分完成！\n拓扑结构文件：{topology_output_path}\n节点信息文件：{nodes_output_path}")

if __name__ == "__main__":
    import os
    
    # 基础目录（当前脚本所在目录）
    base_dir = os.path.dirname(__file__)
    
    # 输入文件路径（自动拼接）
    omnet_path = os.path.join(base_dir, "omnet.json")
    
    # 输出文件路径（定义输出目录，确保目录存在）
    # output_dir = os.path.join(base_dir, "output")  # 输出到单独的output目录
    # os.makedirs(output_dir, exist_ok=True)  # 自动创建目录（若不存在）
    
    device_path = os.path.join(base_dir, "new_omnet_device.json")
    topo_path = os.path.join(base_dir, "new_topology.json")
    
    # 执行拆分
    split_omnet_json(
        omnet_path,
        device_path,
        topo_path
    )