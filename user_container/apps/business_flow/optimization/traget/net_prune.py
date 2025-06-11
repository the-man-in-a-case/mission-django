import networkx as nx
# import matplotlib.pyplot as plt
import time
from collections import defaultdict
import itertools
import math

class NetManager():
    def __init__(self, G):
        if G is not None:
            self.G = G
        else:
            self.G = None
            if not self.load_network():
                self.generate_scale_free_network()
            
    def get_net_info(self):
        return {
            "nodes": self.G.number_of_nodes(),
            "edges": self.G.number_of_edges()
            }

    def generate_scale_free_network(self, num_nodes=102, m=2, filename='scale_free_network.adjlist'):
        """
        生成无标度网络并持久化存储
        
        参数:
        num_nodes: 节点数量
        m: BA模型中每个新节点连接的边数
        filename: 持久化文件名
        """
        # 生成BA无标度网络
        self.G = nx.barabasi_albert_graph(num_nodes, m)
        
        # 保存网络到文件
        nx.write_adjlist(self.G, filename)
        print(f"网络已保存到 {filename}")
        return True

    def load_network(self, filename='scale_free_network.adjlist'):
        """
        从文件加载网络
        
        参数:
        filename: 网络文件路径
        """
        try:
            self.G = nx.read_adjlist(filename)
            print(f"成功加载网络: {filename}")
            return True
        except FileNotFoundError:
            print(f"错误：文件 {filename} 未找到")
            return False
        
    def delete_node_by_list(self, ia_list):
        print(f"remove: {ia_list}")
        self.G.remove_nodes_from(ia_list)
        
    def visualize(self, G=None):
        if G is None:
            G = self.G
        pos = nx.spring_layout(G, seed=42)
        node_size = [n * 15 for _, n in G.degree()]
        # 绘制节点和边
        # plt.figure(figsize=(10, 8))
        nx.draw_networkx_nodes(
            G, pos, 
            node_size=node_size,
            node_color='skyblue',
            alpha=0.7
        )
        nx.draw_networkx_edges(
            G, pos, 
            # width=edge_width,
            edge_color='grey',
            # edge_cmap=plt.cm.viridis,
            alpha=0.6
        )
        nx.draw_networkx_labels(G, pos, font_size=10, font_color='black')
        # plt.title("Scale-Free Network Visualization")
        # plt.show()

class ImportanceAlgorithm():
    """
    重要性排序算法
    """
    def __init__(self):
        pass

    # def start_all(self, graph):
    #     p_hba = multiprocessing.Process(target=self.centrality, args=(graph,))

    #     p_hba.start()
    #     p_hba.join()

    def degree_centrality(self, G):
        """
        计算节点的度中心性，反映局部连接数量。
        """
        s = time.perf_counter()
        centrality = nx.degree_centrality(G)
        nodelist = sorted(centrality, key=centrality.get, reverse=True)
        e = time.perf_counter()
        return nodelist, e-s
    
    def betweenness_centrality(self, G):
        """介数中心性"""
        s = time.perf_counter()
        centrality = nx.betweenness_centrality(G, normalized=True, endpoints=False)
        nodelist = sorted(centrality, key=centrality.get, reverse=True)
        e = time.perf_counter()
        return nodelist, e-s
    
    def pagerank_centrality(self, G, alpha=0.85):
        """
        计算节点的 PageRank 值，反映全局影响力。
        """
        s = time.perf_counter()
        centrality = nx.pagerank(self, G, alpha=alpha)
        nodelist = sorted(centrality, key=centrality.get, reverse=True)
        e = time.perf_counter()
        return nodelist, e-s
    
    def closeness_centrality(self, G):
        """
        接近中心性（Closeness Centrality）
        计算节点的接近中心性，反映节点到其他节点的平均距离。
        """
        s = time.perf_counter()
        centrality = nx.closeness_centrality(G)
        nodelist = sorted(centrality, key=centrality.get, reverse=True)
        e = time.perf_counter()
        return nodelist, e-s
    
    # def kcore_centrality(self, G):
    #     """
    #     计算节点的 k-core 值，衡量节点在核心子图中的位置。
    #     """
    #     s = time.perf_counter()
    #     centrality = nx.core_number(G)
    #     nodelist = sorted(centrality, key=centrality.get, reverse=True)
    #     e = time.perf_counter()
    #     return nodelist, e-s
    def kcore_centrality(self, G):
        """
        计算节点的 k-core 值，衡量节点在核心子图中的位置。
        """
        s = time.perf_counter()
        # 关键修改：将多重图转换为简单图（去重边）
        G_simple = nx.Graph(G)  # 转换为简单图
        centrality = nx.core_number(G_simple)  # 使用转换后的简单图计算核心数
        nodelist = sorted(centrality, key=centrality.get, reverse=True)
        e = time.perf_counter()
        return nodelist, e-s
    
    def collective_influence(self, G):
        """
        集聚影响力（Collective Influence, CI）
        计算节点的 CI 值，结合 k-shell 分解和邻居度数。
        公式: CI(i) = (k_i - 1) * sum(k_j) for j in neighbors
        """
        s = time.perf_counter()
        ci = {}
        for node in G.nodes():
            neighbors = list(G.neighbors(node))
            if not neighbors:
                ci[node] = 0
            else:
                ci[node] = (G.degree(node) - 1) * sum(G.degree(n) for n in neighbors)
        nodelist = sorted(ci, key=ci.get, reverse=True)
        e = time.perf_counter()
        return nodelist, e-s
    
    def robustness(self, G, node_order, show_plt=False, algo_label=""):
        """
        计算复杂网络中节点重要性排序算法的鲁棒性指标 R。
        R 是 σ-p 曲线下的面积，其中 σ 表示删除 p 比例节点后最大连通集团的规模。
        通过从空网络逐步添加节点的方式高效计算 R。

        :param G: 图的邻接表
        :param node_order: 节点的添加顺序（按重要性从高到低排序）
        :param show_plt: 显示鲁棒性面积曲线图
        :param algo_label: 若显示曲线图，则图上标注
        :return: 鲁棒性指标 R
        """
        node_order = node_order[::-1]
        NodeCluster = {}  # 节点 -> 集团 ID
        ClusterNodes = {}  # 集团 ID -> 节点集合
        max_cluster_size = []  # 每次添加节点后最大集团的大小
        total_nodes = len(node_order)
        current_max_size = 0

        for i, vi in enumerate(node_order):
            Ci = set()  # 当前节点 vi 的邻居所在的集团 ID 集合
            # 检查 vi 的邻居是否已存在于当前网络中
            for neighbor in list(G.adj.get(vi, {})):
                
                if neighbor in NodeCluster:
                    Ci.add(NodeCluster[neighbor])
            # 合并集团
            if not Ci:
                # 没有邻居，创建新集团
                new_id = i + 1
                NodeCluster[vi] = new_id
                ClusterNodes[new_id] = {vi}
                candidate_size = 1
            else:
                # 合并所有相关集团，以最小 ID 为标识
                min_id = min(Ci)
                merged_nodes = set()
                for cid in Ci:
                    merged_nodes.update(ClusterNodes[cid])
                    del ClusterNodes[cid]
                merged_nodes.add(vi)
                ClusterNodes[min_id] = merged_nodes
                for node in merged_nodes:
                    NodeCluster[node] = min_id
                candidate_size = len(merged_nodes)
            current_max_size = max(current_max_size, candidate_size)
            max_cluster_size.append(current_max_size)
        sigma_list = [size / total_nodes for size in max_cluster_size] # 纵坐标比例
        p_values = [i / total_nodes for i in range(total_nodes)] # 横坐标比例
        R = 0
        for i in range(1, total_nodes):
            dp = p_values[i] - p_values[i - 1]
            avg_sigma = (sigma_list[i] + sigma_list[i - 1]) / 2
            R += avg_sigma * dp

        # if show_plt:
        #     # 绘制 σ-p 曲线
        #     plt.figure(figsize=(8, 5))
        #     plt.plot(p_values, sigma_list[::-1], color='blue', label='σ-p curve')

        #     # 填充曲线下面积（鲁棒性 R）
        #     plt.fill_between(p_values, sigma_list[::-1], color='skyblue', alpha=0.5, label='Robustness R')

        #     plt.title(f"{algo_label} Robustness Area (σ-p Curve)")
        #     plt.xlabel('Proportion of Removed Nodes (p)')
        #     plt.ylabel('Largest Cluster Size (σ)')
        #     plt.grid(True)
        #     plt.legend()
        #     plt.tight_layout()
            # plt.show()
        return R

    def pagerank_centrality(self, G, alpha=0.85):
        """
        计算节点的 PageRank 值，反映全局影响力。
        """
        s = time.perf_counter()
        centrality = nx.pagerank(G, alpha=alpha)  # 修正：第一个参数应为图 G 而非 self
        nodelist = sorted(centrality, key=centrality.get, reverse=True)
        e = time.perf_counter()
        return nodelist, e-s
    
class NetPrune():
    """
    gamma: 计算置信度权重用的微调参数，越大对算法鲁棒性越敏感
    G: 传入的 nx.Graph，不传入则默认生成一个无标度测试网络并持久化
    """
    def __init__(self, gamma=2, G=None):
        self.NM = NetManager(G)
        self.IA = ImportanceAlgorithm()
        self.gamma = gamma


    def get_net(self)->nx.Graph:
        return self.NM.G
    
    def get_net_info(self)->dict:
        return self.NM.get_net_info()

    def visualize(self)->None:
        return self.NM.visualize()

    def permutation(self):
        nodes = list(self.NM.G.nodes())
        return itertools.permutations(nodes)
    
    def _get_round_result(self, show_plt=False)->list[dict]:
        """
        {
            "name": algo str,
            "r": robust area,
            "order": list
        }
        """
        # 对比排序算法鲁棒性R，R越小代表当前排序越有效，破坏效果好
        round_result = []
        ia_list, _ = self.IA.degree_centrality(self.NM.G)
        round_result.append({
            "name": "degree_centrality",
            "r": self.IA.robustness(self.NM.G, ia_list, show_plt, "Degree Centrality"),
            "order": ia_list
            })
        ia_list, _ = self.IA.betweenness_centrality(self.NM.G)
        round_result.append({
            "name": "betweenness_centrality",
            "r": self.IA.robustness(self.NM.G, ia_list, show_plt, "Betweenness Centrality"),
            "order": ia_list
            })
        ia_list, _ = self.IA.closeness_centrality(self.NM.G)
        round_result.append({
            "name": "closeness_centrality",
            "r": self.IA.robustness(self.NM.G, ia_list, show_plt, "Closeness Centrality"),
            "order": ia_list
            })
        ia_list, _ = self.IA.kcore_centrality(self.NM.G)
        round_result.append({
            "name": "kcore_centrality",
            "r": self.IA.robustness(self.NM.G, ia_list, show_plt, "Kcore Centrality"),
            "order": ia_list
            })
        ia_list, _ = self.IA.collective_influence(self.NM.G)
        round_result.append({
            "name": "collective_influence",
            "r": self.IA.robustness(self.NM.G, ia_list, show_plt, "Collective Influence"),
            "order": ia_list
            })
        return round_result
    
    def _calculate_importance_confidence_level(self, show_plt=False):
        """
        计算节点重要性置信度，返回节点排序与置信度列表（重要性从高到低）
        加权排序融合问题，当前算法：
        1/(r^gamma) * (N-rank)，越大排名越前
        详见加权排序融合
        """
        round_results = self._get_round_result(show_plt)
        
        node_score = defaultdict(float)
        N = self.NM.get_net_info().get("nodes")
        for res in round_results:
            r = res.get("r")
            ranking = res.get("order")
            weight = 1/(r**self.gamma)
            for idx, node in enumerate(ranking):
                node_score[node] += weight * (N - idx)
        
        sorted_confidence = sorted(node_score.items(), key=lambda x: -x[1])
        return sorted_confidence, round_results
            
    def prune_net(self, count=1, show_plt=False):
        """
        网络剪枝
        count: 需要剪去的节点数量
        show_plt: 是否显示不同算法中间结果鲁棒性 σ-p 图
        """
        current_nodes = self.get_net_info().get("nodes")
        if count >= current_nodes:
            raise IndexError(f"prune_net count {count} out of current net nodes: {current_nodes}")
        sorted_confidence, round_results = self._calculate_importance_confidence_level(show_plt)
        # print([node for node, _confidence in sorted_confidence])
        self.NM.delete_node_by_list([node for node, _confidence in sorted_confidence][-count:])
        return round_results
    
    def compute_centrality_orders(self, G: nx.Graph, ret="default") -> dict:
        """
        API 接口：输入 NetworkX 图对象，返回各中心性排序字典
        
        Args:
            G: NetworkX 图对象（简单图或多重图，需确保与中心性算法兼容）
            
        Returns:
            dict: 包含各中心性排序的字典，格式示例：
                {
                    "degree_centrality order": [node1, node2, ...],
                    "betweenness_centrality order": [node1, node2, ...],
                    ...
                }
        """
        ia = ImportanceAlgorithm()
        result = {}

        # 计算并存储各中心性排序
        degree_order, _ = ia.degree_centrality(G)
        result["degree_centrality order"] = degree_order
        if ret == "node":
            result = {
                "degree_centrality order": degree_order,  
            }
            return result
        # 计算 PageRank 中心性
        betweenness_order, _ = ia.betweenness_centrality(G)
        result["betweenness_centrality order"] = betweenness_order
        
        closeness_order, _ = ia.closeness_centrality(G)
        result["closeness_centrality order"] = closeness_order
        
        kcore_order, _ = ia.kcore_centrality(G)
        result["kcore_centrality order"] = kcore_order
        
        ci_order, _ = ia.collective_influence(G)
        result["collective_influence order"] = ci_order
        
        return result

# if __name__ == "__main__":
    
#     # net_prune = NetPrune(gamma=2)

#     # # 排列组合
#     # print(f"permutation total count: {math.factorial(net_prune.get_net_info().get('nodes'))}")
#     # # permutation = net_prune.permutation()
#     # # for perm in permutation:
#     # #     print(perm)
        
#     # cnt = 1
#     # print(f"net nodes: {net_prune.get_net_info().get('nodes')}")
#     # try:
#     #     res = net_prune.prune_net(count=1, show_plt=False)
#     #     for v in res:
#     #         print(f"{v.get('name')} order: {v.get('order')}")
#     #     print(f"Round {cnt}, nodes left: {net_prune.get_net_info().get('nodes')}")
#     #     net_prune.visualize()
#     #     cnt += 1
#     # except IndexError:
#     #     print("End of net prune!")
#     #     pass
#         # 示例用法：输入 NetworkX 图对象，获取排序字典
#     import networkx as nx
    
#     # 示例图（可替换为用户实际图对象）
#     G = nx.barabasi_albert_graph(n=25, m=2)  # 生成一个简单无标度图
    
#     # 初始化 NetPrune 并调用 API
#     net_prune = NetPrune()
#     centrality_orders = net_prune.compute_centrality_orders(G)
    
#     # 打印结果（可注释或删除）
#     print("各中心性排序结果：")
#     for key, order in centrality_orders.items():
#         print(f"{key}: {order}")