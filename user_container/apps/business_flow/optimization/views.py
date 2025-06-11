from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from .traget.net_prune import NetPrune  # 注意路径是否正确（可能需修正为target）
from .target_optimization import TargetOptimization  # 复用拓扑加载逻辑
from resource.models import Industry, Simulator, Facility, FacilityType, FacilityParameter
import networkx as nx
from django.db.models import F  # 用于字段引用
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from networkx.readwrite import json_graph
from django.db.models import ObjectDoesNotExist
from course.models import Task  # 假设任务模型在course应用中
from .target_optimization import TargetOptimization  # 复用现有优化类
import networkx as nx
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
import logging

logger = logging.getLogger(__name__)

class IndustryNodeOptimizeAPI(APIView):

    """
    curl "http://localhost:8000/mission/optimization/api/industry-node-optimize/?industry_code=IND001"
{
    "industry_code": "IND001",
    "optimized_nodes": [
        {
            "node_id": "a1b2c3d4-...",
            "node_name": "变电站A",
            "node_type": "电力设施",
            "node_parameters": {"电压等级": "220kV", "容量": "500MVA"}
        },
        {
            "node_id": "e5f6g7h8-...",
            "node_name": "通信基站B",
            "node_type": "通信设施",
            "node_parameters": {"频段": "2.6GHz", "覆盖半径": "3km"}
        }
    ]
}
    """
    @swagger_auto_schema(
        operation_summary="行业节点优化",
        operation_description="根据行业编号返回优化后的节点参数（如电压、容量等）",
        manual_parameters=[
            openapi.Parameter(
                name="industry_code",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description="行业编号（如001）"
            )
        ],
        responses={
            200: openapi.Response("优化节点列表", openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    "industry_code": openapi.Schema(type=openapi.TYPE_STRING, description="行业编号"),
                    "optimized_nodes": openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "node_id": openapi.Schema(type=openapi.TYPE_STRING),
                                "node_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "node_parameters": openapi.Schema(type=openapi.TYPE_OBJECT)
                            }
                        )
                    )
                }
            )),
            400: openapi.Response("缺少行业编号参数"),
            404: openapi.Response("行业无关联模拟器")
        }
    )
    def get(self, request):
        # 1. 验证行业参数
        industry_code = request.query_params.get("industry_code")
        if not industry_code:
            return Response(
                {"error": "请提供industry_code参数（行业ID）"}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. 获取行业拓扑图（复用target_optimization的加载逻辑）
        try:
            # 从数据库获取行业关联的模拟器
            simulator = Simulator.objects.filter(industry__industry_id=industry_code).first()
            if not simulator:
                return Response(
                    {"error": f"行业{industry_code}无关联模拟器"}, 
                    status=status.HTTP_404_NOT_FOUND
                )

            # 动态调用拓扑加载函数（如load_opendss_topo）
            load_func_name = f"load_{simulator.simulator_name.lower()}_topo"
            load_func = getattr(TargetOptimization, load_func_name, None)
            if not load_func:
                return Response(
                    {"error": f"未找到模拟器{simulator.simulator_name}的加载函数"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # 加载拓扑图（假设配置数据包含拓扑文件路径）
            graph = load_func({"topo_file_path": simulator.template_path})  # 需与target_optimization的参数格式一致
            if not graph or not isinstance(graph, nx.Graph):
                return Response(
                    {"error": "拓扑图加载失败或格式错误"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Industry.DoesNotExist:
            return Response(
                {"error": f"行业{industry_code}不存在"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"拓扑加载失败: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 3. 调用net_prune计算节点排序（ret='node'）
        try:
            net_prune = NetPrune()
            centrality_result = net_prune.compute_centrality_orders(graph, ret="node")
            node_ids = centrality_result.get("degree_centrality order", [])  # 取度中心性排序结果（可根据需求调整）
        except Exception as e:
            return Response(
                {"error": f"节点排序计算失败: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # 4. 查询数据库获取节点参数（FacilityParameter关联数据）
        try:
            # 使用select_related优化查询（减少数据库查询次数）
            facilities = Facility.objects.select_related("facility_type").filter(
                facility_id__in=node_ids  # 仅查询排序中的节点
            )
            # 预取设施参数（每个设施可能有多个参数，取最新或主参数）
            facility_params = []
            for facility in facilities:
                param = FacilityParameter.objects.filter(facility=facility).first()
                facility_params.append({
                    "node_id": str(facility.facility_id),  # UUID转字符串
                    "node_name": facility.facility_name,
                    "node_type": facility.facility_type.type_name,  # 设施类名称
                    "node_parameters": param.parameter_data if param else {}  # 参数数据
                })

            return Response({
                "industry_code": industry_code,
                "optimized_nodes": facility_params  # 包含参数的节点字典列表
            })

        except Facility.DoesNotExist:
            return Response(
                {"error": "部分节点信息不存在于数据库"}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": f"节点参数查询失败: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
            
class OptimizedPathHighlightView(APIView):
    """DRF接口：获取优化路径在原Graph中的高亮JSON数据"""
    @swagger_auto_schema(
        operation_summary="获取优化路径高亮数据",
        operation_description="通过task_id获取各行业优化路径的原Graph高亮JSON数据（包含节点/边的is_optimized标记）",
        manual_parameters=[
            openapi.Parameter(
                name="task_id",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                required=True,
                description="任务ID（UUID格式）"
            )
        ],
        responses={
            200: openapi.Response(
                "成功响应",
                openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "message": openapi.Schema(type=openapi.TYPE_STRING, description="提示信息"),
                        "data": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            description="行业编号到高亮路径JSON的映射",
                            additional_properties=openapi.Schema(
                                type=openapi.TYPE_ARRAY,
                                items=openapi.Schema(
                                    type=openapi.TYPE_OBJECT,
                                    properties={
                                        "directed": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                        "nodes": openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(
                                                type=openapi.TYPE_OBJECT,
                                                properties={
                                                    "id": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "is_optimized": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                                                    "voltage": openapi.Schema(type=openapi.TYPE_STRING, description="电压等级")
                                                }
                                            )
                                        ),
                                        "links": openapi.Schema(
                                            type=openapi.TYPE_ARRAY,
                                            items=openapi.Schema(
                                                type=openapi.TYPE_OBJECT,
                                                properties={
                                                    "source": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "target": openapi.Schema(type=openapi.TYPE_STRING),
                                                    "is_optimized": openapi.Schema(type=openapi.TYPE_BOOLEAN)
                                                }
                                            )
                                        )
                                    }
                                )
                            )
                        )
                    }
                )
            ),
            400: openapi.Response("参数缺失", openapi.Schema(type=openapi.TYPE_STRING)),
            404: openapi.Response("任务不存在", openapi.Schema(type=openapi.TYPE_STRING)),
            500: openapi.Response("服务器错误", openapi.Schema(type=openapi.TYPE_STRING))
        }
    )
    
    def get(self, request):
        try:
            # 1. 参数验证（必须传入task_id）
            task_id = request.query_params.get('task_id')
            if not task_id:
                raise ValidationError("缺少必要参数：task_id")

            # 2. 查询关联的任务和场景（假设任务与场景存在外键关系）
            try:
                task = Task.objects.get(task_id=task_id)
                scene = task.scene  # 假设任务对象有scene属性关联场景
            except ObjectDoesNotExist:
                return Response(
                    {"error": "任务或关联场景不存在"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # 3. 初始化优化类并获取关键数据
            optimizer = TargetOptimization(scene, task)
            optimized_paths = optimizer.target_optimization(optimizer.target_list())  # 获取优化路径字典
            original_graphs = optimizer.network_graph  # 直接使用已加载的原Graph（来自_create_network_graph）

            # 4. 处理每个行业的路径高亮
            result = {}
            for industry_code, paths in optimized_paths.items():
                # 跳过无效路径
                # if not paths or industry_code not in original_graphs:
                #     result[industry_code] = None
                #     continue
                if industry_code not in original_graphs:
                    result[industry_code] = None
                    logger.warning(f"行业{industry_code}无关联拓扑图")
                    continue
                if not paths:
                    result[industry_code] = None
                    logger.info(f"行业{industry_code}无有效优化路径")
                    continue

                # 获取原Graph和当前行业的所有路径
                original_graph = original_graphs[industry_code]
                highlighted_subgraphs = []

                # 处理每条路径（假设paths是[[node1,node2...], [node3,node4...]]格式）
                for path in paths:
                    # 提取路径对应的子图（包含路径中的节点和连接边）
                    path_subgraph = original_graph.subgraph(path)
                    
                    # 添加高亮标记（节点和边）
                    for node in path_subgraph.nodes:
                        path_subgraph.nodes[node]['is_optimized'] = True
                    for u, v in path_subgraph.edges:
                        path_subgraph.edges[u, v]['is_optimized'] = True

                    # 转换为node_link_data格式
                    highlighted_subgraphs.append(json_graph.node_link_data(path_subgraph))

                result[industry_code] = highlighted_subgraphs

            return Response(
                {"message": "成功获取高亮路径数据", "data": result},
                status=status.HTTP_200_OK
            )

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response(
                {"error": f"服务器内部错误：{str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )