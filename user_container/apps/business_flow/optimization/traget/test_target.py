import os
import networkx as nx
import re   

def load_opendss_topo(folder_path):
    # 初始化多重图（允许节点间存在多条边）
    G = nx.MultiGraph()

    # 遍历文件夹中的所有文件
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # 跳过非DSS文件
        if not filename.endswith('.dss'):
            continue

        # 处理母线电压基准文件（confirm_kv_bases.dss）
        if filename == 'confirm_kv_bases.dss':
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # 匹配setkvbase命令格式：setkvbase bus=母线名 kVLL=电压值
                    match = re.match(r'setkvbase\s+bus=(\w+)\s+kVLL=([\d.]+)', line.strip())
                    if match:
                        bus_name = match.group(1)
                        kvll = float(match.group(2))
                        # 添加节点并记录电压属性
                        G.add_node(bus_name, kvll=kvll)

        # 处理变压器文件（transformers.dss）
        elif filename == 'transformers.dss':
            with open(file_path, 'r', encoding='utf-8') as f:
                # 合并续行（DSS文件中用~表示续行）
                full_content = f.read().replace('\n~', ' ').replace('~', ' ')
                # 分割每个变压器定义（匹配"New Transformer."开头的块）
                transformer_blocks = re.findall(r'New Transformer\.\w+.*?(?=New Transformer\.|\Z)', 
                                            full_content, re.DOTALL)
        
                for block in transformer_blocks:
                    # 提取变压器参数
                    params = {}
                    # 匹配变压器名称（New Transformer.<name>）
                    name_match = re.search(r'New Transformer\.(\w+)', block)
                    if not name_match:
                        continue
                    transformer_name = name_match.group(1)
            
                    # 提取buses参数（格式：buses=[bus1, bus2]）
                    buses_match = re.search(r'buses=\[([\w, ]+)\]', block)
                    if buses_match:
                        buses = [b.strip() for b in buses_match.group(1).split(',')]
                        if len(buses) != 2:
                            continue  # 只处理双绕组变压器
                        bus1, bus2 = buses
                
                        # 提取其他参数（kVA, Xhl等）
                        params['type'] = 'transformer'
                        params['name'] = transformer_name
                        params['kVA'] = float(re.search(r'kVA=([\d.]+)', block).group(1)) if re.search(r'kVA=([\d.]+)', block) else None
                        params['Xhl'] = float(re.search(r'Xhl=([\d.]+)', block).group(1)) if re.search(r'Xhl=([\d.]+)', block) else None
                
                        # 添加边（使用变压器名称作为边的唯一key）
                        G.add_edge(bus1, bus2, key=transformer_name, **params)

    return G


G = load_opendss_topo('I:\代码库\项目开发\sim_conf\opendss_client_topo_conf')
all_nodes = list(G.nodes())  # 或 list(G.nodes)
print(all_nodes)  # 输出: [1, 2, 3, 'A', 'B']

# from net_prune import NetPrune
# NetPrune(G=G)
# rest = NetPrune(G=G).compute_centrality_orders(G)
# print(list(rest.values()))