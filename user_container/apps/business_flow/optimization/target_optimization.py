# mission/optimization/target_optimization.py
import logging
from django.db import transaction
from course.models import TaskResult
from resource.models import Facility, ThreatImpact
from .traget.net_prune import NetPrune
import math
from .traget.opendss_to_networkx import load_opendss_topo  # 假设G是从opendss_to_networkx.py中导入的图对象
from .traget.omnet_to_networkx import load_omnet_topo
from concurrent.futures import ThreadPoolExecutor  # 新增多线程导入
from django.core.exceptions import ObjectDoesNotExist  # 新增异常处理导入
from resource.models import Simulator  # 新增模拟器模型导入
import itertools  # 新增排列生成库
import networkx as nx  # 新增网络分析库
import uuid  # 用于生成唯一的工作ID


logger = logging.getLogger(__name__)

class TargetOptimization:
    def __init__(self, scene, task):
        self.scene = scene
        self.task = task
        self.network_graph = self._create_network_graph()  # 创建网络拓扑图 {“001”： G1}
        # self.net_prune = net_prune(self.network_graph)  # 初始化网络修剪对象
        self.all_nodes = {}  # {"001": [node1, node2...], "002": [...]}
        self.all_paths = {}  # {"001": [[path1], [path2]...], "002": [...]}
        self.net_prune = NetPrune()
    
    def target_list(self):
        """生成目标列表（包含各行业节点和路径信息）"""
        try:
            # 使用多线程处理各行业拓扑
            with ThreadPoolExecutor(max_workers=6) as executor:
                # 提交所有行业的处理任务
                futures = []
                for industry_code, graph in self.network_graph.items():
                    futures.append(executor.submit(
                        self._process_single_industry, 
                        industry_code, 
                        graph
                    ))
                
                # 收集结果
                for future in futures:
                    industry_code, nodes, paths = future.result()
                    self.all_nodes[industry_code] = nodes
                    self.all_paths[industry_code] = paths

            # 去重目标列表（原逻辑，可根据需求调整）
            targets = list(set([node for nodes in self.all_nodes.values() for node in nodes]))
            
            # 创建任务结果记录（原有逻辑）
            self._create_task_result(targets, all_paths=self.all_paths)

            return targets

        except Exception as e:
            logger.error(f"Error generating target list: {str(e)}")
            raise

    def _process_single_industry(self, industry_code, graph):
        """处理单个行业拓扑，生成节点列表和所有可能删除路径"""
        try:
            # 1. 获取节点列表
            nodes = list(graph.nodes())
            if not nodes:
                return (industry_code, [], [])

            # 2. 生成所有可能的节点删除路径（全排列）
            # 注意：节点较多时排列数会指数级增长，建议根据实际需求调整逻辑
            # 示例逻辑：生成所有可能的节点删除顺序（即节点的全排列）
            # paths = list(itertools.permutations(nodes))
            paths = []
            for source in nodes:
                for target in nodes:
                    if source != target:
                        for path in nx.all_simple_paths(graph, source=source, target=target, cutoff=5):
                            paths.append(path)
            
            # 可选优化：如果需要简单路径（非全排列），可使用networkx的all_simple_paths
            # 例如：paths = [list(path) for path in nx.all_simple_paths(graph, source=nodes[0], target=nodes[-1])]
            
            return (industry_code, nodes, paths)

        except Exception as e:
            logger.error(f"处理行业{industry_code}拓扑时出错: {str(e)}")
            return (industry_code, [], [])  # 出错时返回空列表
    
    # def _get_targets_from_templates(self):
    #     """从行业数据模板获取目标"""
    #     targets = []
        
    #     for industry_id in range(1, 7):  # 假设有6个行业
    #         template_field = f'industry_{industry_id:03d}_template'
    #         template_data = getattr(self.scene, template_field, None)
            
    #         if template_data and 'nodes' in template_data:
    #             for node in template_data['nodes']:
    #                 if 'name' in node:
    #                     targets.append(node['name'])
        
    #     return targets
    
    # def _get_targets_from_middleware(self):
    #     """从中间件配置获取目标"""
    #     targets = []
        
    #     for config in self.scene.middleware_configs.all():
    #         if config.attribute_name not in targets:
    #             targets.append(config.attribute_name)
        
    #     return targets
    def _create_network_graph(self):
        """
        创建多配置网络拓扑图（支持001-006配置）
        使用多线程并行加载有效配置的拓扑
        
        Returns:
            dict: 格式 {"001": G1, "002": G2, ...}，无效配置不包含在结果中
        """
        network_graphs = {}
        config_numbers = [f"{i:03d}" for i in range(1, 7)]  # 生成001-006配置编号

        # 定义加载单个配置的函数（用于多线程）
        def load_single_config(config_number):
            try:
                # 1. 从scene对象获取配置字段（假设字段名格式为industry_{num}_config）
                config_field = f'industry_{config_number}_config'
                config_data = getattr(self.scene, config_field, None)
                
                if not config_data:
                    logger.info(f"配置{config_number}为空，跳过加载")
                    return None

                # 2. 获取对应模拟器信息（假设配置中包含simulator_id）
                simulator_id = config_data.get('simulator_id')
                if not simulator_id:
                    logger.warning(f"配置{config_number}缺少simulator_id，跳过加载")
                    return None

                # 3. 查询模拟器模型获取模拟器名称
                simulator = Simulator.objects.get(simulator_id=simulator_id)
                simulator_name = simulator.simulator_name.lower()  # 转换为小写匹配函数名

                # 4. 动态获取对应的加载函数（如load_opendss_topo -> simulator_name=opendss）
                load_func = getattr(self, f'load_{simulator_name}_topo', None)
                if not load_func:
                    logger.error(f"未找到模拟器{simulator_name}对应的加载函数load_{simulator_name}_topo")
                    return None

                # 5. 执行加载函数（传入配置数据中的拓扑文件路径）
                graph = load_func(config_data)
                return (config_number, graph)

            except ObjectDoesNotExist:
                logger.error(f"配置{config_number}对应的模拟器ID{simulator_id}不存在")
                return None
            except Exception as e:
                logger.error(f"加载配置{config_number}时发生异常: {str(e)}")
                return None

        # 使用线程池并行加载（最多5个线程）
        with ThreadPoolExecutor(max_workers=6) as executor:
            futures = [executor.submit(load_single_config, num) for num in config_numbers]
            
            # 收集有效结果
            for future in futures:
                result = future.result()
                if result:  # 过滤None结果
                    config_number, graph = result
                    network_graphs[config_number] = graph

        return network_graphs


    def _create_task_result(self, targets, paths):
        """创建任务结果记录"""
        with transaction.atomic():
            TaskResult.objects.update_or_create(
                task=self.task,
                scene=self.scene,
                defaults={
                    'attack_target': targets,
                    'attack_path': paths
                }
            )
    
    def target_optimization(self, targets):
        """
        优化目标列表
        
        Args:
            targets: 目标列表
        
        Returns:
            dict: 优化后的目标字典
        """
        try:
            optimized_paths = {}
            taskresult = []
            # # 获取每个目标的影响值
            # for target in targets:
            #     impact_value = self._get_target_impact(target)
            #     optimized_targets[target] = impact_value
            
             # 使用多线程处理各行业拓扑优化
            with ThreadPoolExecutor(max_workers=6) as executor:
                # 提交所有行业的优化任务
                futures = []
                for industry_code, graph in self.network_graph.items():
                    # 提交任务：(行业编号, 图对象) -> 优化路径
                    futures.append(executor.submit(
                        self._optimize_single_industry,
                        industry_code,
                        graph
                    ))
                
                # 收集优化结果
                for future in futures:
                    industry_code, paths = future.result()
                    optimized_paths[industry_code] = paths
                    # 生成唯一 work_id（使用 uuid 确保唯一性）
                    work_id = uuid.uuid4().hex
                    # 获取当前任务的 task_id（从类属性中获取）
                    task_id = self.task.task_id
                    # 构造元组并添加到 taskresult
                    taskresult.append( (work_id, task_id, industry_code, paths) )
    
      
            # 更新任务结果（包含优化目标和路径）
            self._update_task_result(targets, optimized_paths)
            
            return optimized_paths

        except Exception as e:
            logger.error(f"Error optimizing targets: {str(e)}")
            raise

    def _optimize_single_industry(self, industry_code, graph):
        """处理单个行业的拓扑优化"""
        try:
            # 调用NetPrune计算中心性排序（优化路径）
            optimized_path = list(self.NetPrune.compute_centrality_orders(graph).values())
            return (industry_code, optimized_path)
        except Exception as e:
            logger.error(f"行业{industry_code}拓扑优化失败: {str(e)}")
            return (industry_code, None)  # 失败时返回None

    def _get_target_impact(self, target):
        """获取目标的影响值"""
        try:
            # 查找对应的设施
            facilities = Facility.objects.filter(facility_name__icontains=target)
            
            if facilities.exists():
                facility = facilities.first()
                
                # 查找威胁影响
                try:
                    threat = ThreatImpact.objects.get(facility=facility)
                    return threat.impact_value
                except ThreatImpact.DoesNotExist:
                    # 如果没有找到威胁影响，使用默认值
                    return 0.5
            else:
                # 如果没有找到设施，使用默认值
                return 0.5
        
        except Exception as e:
            logger.warning(f"Error finding impact for target {target}: {str(e)}")
            return 0.5
    
    def _update_task_result(self, optimized_targets, optimized_paths):
        """更新任务结果的攻击目标"""
        with transaction.atomic():
            for result in TaskResult.objects.filter(task=self.task, scene=self.scene):
                result.attack_target = optimized_targets
                result.attack_path = optimized_paths
                result.save()