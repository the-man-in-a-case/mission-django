import os
import re
import networkx as nx

def load_opendss_topo(file_contents):
    """
    从opendss_client_topo_conf文件夹加载拓扑数据并构建NetworkX图
    
    Args:
        folder_path (str): opendss_client_topo_conf文件夹路径
    
    Returns:
        nx.MultiGraph: 包含电力系统拓扑的NetworkX多重图实例
    """
    # 初始化多重图（允许节点间存在多条边）
    G = nx.MultiGraph()
    
    # 遍历文件夹中的所有文件
    # for filename in os.listdir(folder_path):
    #     file_path = os.path.join(folder_path, filename)
        
    #     # 跳过非DSS文件
    #     if not filename.endswith('.dss'):
    #         continue
        
    #     # 处理母线电压基准文件（confirm_kv_bases.dss）
    #     if filename == 'confirm_kv_bases.dss':
    #         with open(file_path, 'r', encoding='utf-8') as f:
    #             for line in f:
    #                 # 匹配setkvbase命令格式：setkvbase bus=母线名 kVLL=电压值
    #                 match = re.match(r'setkvbase\s+bus=(\w+)\s+kVLL=([\d.]+)', line.strip())
    #                 if match:
    #                     bus_name = match.group(1)
    #                     kvll = float(match.group(2))
    #                     # 添加节点并记录电压属性
    #                     G.add_node(bus_name, kvll=kvll)
        
    #     # 处理变压器文件（transformers.dss）
    #     elif filename == 'transformers.dss':
    #         with open(file_path, 'r', encoding='utf-8') as f:
    #             # 合并续行（DSS文件中用~表示续行）
    #             full_content = f.read().replace('\n~', ' ').replace('~', ' ')
    #             # 分割每个变压器定义（匹配"New Transformer."开头的块）
    #             transformer_blocks = re.findall(r'New Transformer\.\w+.*?(?=New Transformer\.|\Z)', 
    #                                            full_content, re.DOTALL)
                
    #             for block in transformer_blocks:
    #                 # 提取变压器参数
    #                 params = {}
    #                 # 匹配变压器名称（New Transformer.<name>）
    #                 name_match = re.search(r'New Transformer\.(\w+)', block)
    #                 if not name_match:
    #                     continue
    #                 transformer_name = name_match.group(1)
                    
    #                 # 提取buses参数（格式：buses=[bus1, bus2]）
    #                 buses_match = re.search(r'buses=\[([\w, ]+)\]', block)
    #                 if buses_match:
    #                     buses = [b.strip() for b in buses_match.group(1).split(',')]
    #                     if len(buses) != 2:
    #                         continue  # 只处理双绕组变压器
    #                     bus1, bus2 = buses
                        
    #                     # 提取其他参数（kVA, Xhl等）
    #                     params['type'] = 'transformer'
    #                     params['name'] = transformer_name
    #                     params['kVA'] = float(re.search(r'kVA=([\d.]+)', block).group(1)) if re.search(r'kVA=([\d.]+)', block) else None
    #                     params['Xhl'] = float(re.search(r'Xhl=([\d.]+)', block).group(1)) if re.search(r'Xhl=([\d.]+)', block) else None
                        
    #                     # 添加边（使用变压器名称作为边的唯一key）
    #                     G.add_edge(bus1, bus2, key=transformer_name, **params)
    
    # return G
    required_files = ['confirm_kv_bases.dss', 'transformers.dss']
    for req_file in required_files:
        if req_file not in file_contents:
            raise FileNotFoundError(f"未找到{req_file}文件")

    # 处理母线电压基准文件（confirm_kv_bases.dss）
    for line in file_contents['confirm_kv_bases.dss'].splitlines():
        match = re.match(r'setkvbase\s+bus=(\w+)\s+kVLL=([\d.]+)', line.strip())
        if match:
            bus_name = match.group(1)
            kvll = float(match.group(2))
            G.add_node(bus_name, kvll=kvll)

    # 处理变压器文件（transformers.dss）
    full_content = file_contents['transformers.dss'].replace('\n~', ' ').replace('~', ' ')
    transformer_blocks = re.findall(r'New Transformer\.\w+.*?(?=New Transformer\.|\Z)', full_content, re.DOTALL)

    for block in transformer_blocks:
        params = {}
        name_match = re.search(r'New Transformer\.(\w+)', block)
        if not name_match:
            continue
        transformer_name = name_match.group(1)

        buses_match = re.search(r'buses=\[([\w, ]+)\]', block)
        if not buses_match:
            continue
        buses = [b.strip() for b in buses_match.group(1).split(',')]
        if len(buses) != 2:
            continue  # 只处理双绕组变压器
        bus1, bus2 = buses

        params['type'] = 'transformer'
        params['name'] = transformer_name
        params['kVA'] = float(re.search(r'kVA=([\d.]+)', block).group(1)) if re.search(r'kVA=([\d.]+)', block) else None
        params['Xhl'] = float(re.search(r'Xhl=([\d.]+)', block).group(1)) if re.search(r'Xhl=([\d.]+)', block) else None

        G.add_edge(bus1, bus2, key=transformer_name, **params)

    return G

# # 使用绝对路径
# path =  os.path.join(os.path.dirname(__file__), 'opendss_client_topo_conf')
# graph = load_opendss_topo(path)

# # 验证图信息
# print(f"节点数: {graph.number_of_nodes()}")
# print(f"边数: {graph.number_of_edges()}")
# print("示例节点属性:", graph.nodes['1_riversde'])  # 输出母线电压属性
# print("示例边属性:", graph.get_edge_data('61_wkammer', '64_kammer'))  # 输出变压器参数

# # betweenness = nx.betweenness_centrality(graph, weight=None)
# # degree = dict(graph.degree())
# # import pandas as pd
# # # 创建数据框
# # df = pd.DataFrame({
# #     'node': list(betweenness.keys()),
# #     'betweenness': list(betweenness.values()),
# #     'degree': [degree[node] for node in betweenness.keys()]
# # })
# # print(df.head())  # 打印前5行数据框
# from net_prune  import NetPrune
# net_prune = NetPrune(gamma=2,G=graph)

# # 排列组合
# print(f"permutation total count: {math.factorial(net_prune.get_net_info().get('nodes'))}")
# # permutation = net_prune.permutation()
# # for perm in permutation:
# #     print(perm)
# import math
# cnt = 1
# # print(f"net nodes: {net_prune.get_net_info().get("nodes")}")
# try:
#     res = net_prune.prune_net(count=1, show_plt=False)
#     for v in res:
#         print(f"{v.get("name")} order: {v.get("order")}")
#     print(f"Round {cnt}, nodes left: {net_prune.get_net_info().get("nodes")}")
#     net_prune.visualize()
#     cnt += 1
# except IndexError:
#     print("End of net prune!")
#     pass