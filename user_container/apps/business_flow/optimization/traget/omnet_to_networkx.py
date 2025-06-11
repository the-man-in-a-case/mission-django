import os
import re
import networkx as nx

def load_omnet_topo(file_contents):
    """
    从omnet_client_topo_conf文件夹加载拓扑数据并构建NetworkX图
    
    Args:
        folder_path (str): omnet_client_topo_conf文件夹路径
    
    Returns:
        nx.MultiGraph: 包含OMNeT++拓扑的NetworkX多重图实例
    """
    G = nx.MultiGraph()
    
    # # 遍历文件夹查找topology.ned文件
    # for filename in os.listdir(folder_path):
    #     if filename == "topology.ned":
    #         ned_path = os.path.join(folder_path, filename)
    #         break
    # else:
    #     raise FileNotFoundError("未找到topology.ned文件")

    # # 读取NED文件内容
    # with open(ned_path, 'r', encoding='utf-8') as f:
    #     content = f.read()
    if "topology.ned" not in file_contents:
        raise FileNotFoundError("未找到topology.ned文件")

    content = file_contents["topology.ned"]

    # 提取节点信息（submodules部分）
    node_pattern = re.compile(r'(\w+):\s+(\w+)\s+{', re.MULTILINE)
    for match in node_pattern.finditer(content):
        node_name = match.group(1)
        node_type = match.group(2)
        G.add_node(node_name, type=node_type)

    # 提取连接信息（connections部分）
    edge_pattern = re.compile(r'(\w+)\.out\+\+\s+-->\s+GasPipe\s+-->\s+(\w+)\.in\+\+', re.MULTILINE)
    for match in edge_pattern.finditer(content):
        source = match.group(1)
        target = match.group(2)
        G.add_edge(source, target, type='GasPipe')

    return G

# # 示例用法
# if __name__ == "__main__":
#     # 替换为实际的omnet_client_topo_conf文件夹路径
#     folder_path = os.path.join(os.path.dirname(__file__), 'omnet_client_topo_conf')
#     graph = load_omnet_topo(folder_path)

#     # 验证图信息
#     print(f"节点数: {graph.number_of_nodes()}")
#     print(f"边数: {graph.number_of_edges()}")
#     print("示例节点属性:", graph.nodes['gasNode1'])  # 输出节点类型
#     print("示例边属性:", graph.get_edge_data('gasNode1', 'gasNode2'))  # 输出边类型
#     # betweenness = nx.betweenness_centrality(graph, weight=None)
#     # degree = dict(graph.degree())
#     # import pandas as pd
#     # # 创建数据框
#     # df = pd.DataFrame({
#     #     'node': list(betweenness.keys()),
#     #     'betweenness': list(betweenness.values()),
#     #     'degree': [degree[node] for node in betweenness.keys()]
#     # })
#     # print(df.head())  # 打印前5行数据框
#     # from net_prune  import NetPrune
#     # import math
#     # net_prune = NetPrune(gamma=2,G=graph)

#     # # 排列组合
#     # print(f"permutation total count: {math.factorial(net_prune.get_net_info().get('nodes'))}")
#     # # permutation = net_prune.permutation()
#     # # for perm in permutation:
#     # #     print(perm)
 
#     # cnt = 1
#     # print(f"net nodes: {net_prune.get_net_info().get('nodes')}") 
#     # try:
#     #     res = net_prune.prune_net(count=1, show_plt=False)
#     #     print(res)
#     #     print("-----")
#     #     for v in res:
#     #         print(f"{v.get('name')} order: {v.get('order')}")
#     #     print(f"Round {cnt}, nodes left: {net_prune.get_net_info().get('nodes')}")
#     #     net_prune.visualize()
#     #     cnt += 1
#     # except IndexError:
#     #     print("End of net prune!")
#     # pass
#     import networkx as nx
#     from net_prune import NetPrune

#     # 创建/加载 NetworkX 图
#     # G = nx.read_adjlist("your_graph.adjlist")  # 或其他方式生成图

#     # 调用 API 获取排序结果
#     net_prune = NetPrune()
#     result = net_prune.compute_centrality_orders(graph)
#     print(result)  # 输出目标格式字典