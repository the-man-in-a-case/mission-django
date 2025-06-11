import networkx as nx
from jinja2 import Environment, FileSystemLoader
from ..resourcedb.models import Node, Edge

def build_networkx_graph(layers):
    """根据图层构建networkx图"""
    G = nx.DiGraph()
    for layer in layers:
        # 添加节点
        for node in layer.nodes.all():  # 假设Node模型有layer外键
            G.add_node(node.base_node.id, **node.base_node.attribute)
        # 添加边
        for intra_edge in layer.intra_edges.all():  # 假设IntraEdge模型有layer外键
            edge = intra_edge.edge
            G.add_edge(edge.source_node.id, edge.destination_node.id, **edge.base_edge.attribute)
    return G

def generate_topo_json(graph):
    """将networkx图转换为拓扑JSON"""
    nodes = [{'id': n, 'attrs': d} for n, d in graph.nodes(data=True)]
    edges = [{'source': u, 'target': v, 'attrs': d} for u, v, d in graph.edges(data=True)]
    return {'nodes': nodes, 'edges': edges}

def render_simulation_config(layer, graph):
    """使用jinja2渲染模拟器配置模板"""
    # 假设模板路径在user_container/apps/business_flow/templates
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template(f"{layer.type}_template.j2")  # 按图层类型匹配模板
    return template.render(graph=graph, layer=layer)

def build_networkx_graph_from_area(area_json):
    """从区域JSON构建networkx图"""
    G = nx.DiGraph()
    for node in area_json.get('nodes', []):
        G.add_node(node['id'], **node['attrs'])
    for edge in area_json.get('edges', []):
        G.add_edge(edge['source'], edge['target'], **edge['attrs'])
    return G

def calculate_node_path_combinations(global_graph, area_graph):
    """计算节点和路径组合"""
    # 示例：找到区域图在全局图中的所有子图匹配
    subgraphs = list(nx.algorithms.isomorphism.DiGraphMatcher(global_graph, area_graph).subgraph_isomorphisms_iter())
    return [{'nodes': list(g.keys()), 'edges': list(g.values())} for g in subgraphs]