import queue
from networkx.algorithms.bipartite import projection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from . import tasks
from .project_management import create_project  # 新增导入
from .resource_client import get_all_resources_from_admin  # 新增导入
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from django.db import transaction
from ..resourcedb.models import Layer, Node, Edge  # 假设 resourcedb 包含这些模型
from .influxdb import query_influxdb_data  # 导入封装的查询函数
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from ..resourcedb.models import Template, Project, Map, Technique  # 假设相关模型已存在
from .serializers import TemplateSerializer, TemplateNodeSerializer

class BusinessFlowViewSet(viewsets.GenericViewSet):
    @action(detail=False, methods=['get'], url_path='resource-list')
    def get_resource_list(self, request):
        """获取资源列表（调用独立客户端模块）"""
        try:
            resources = get_all_resources_from_admin()  # 调用独立模块
            return Response(resources)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='import-resource')
    def import_resource(self, request):
        """导入资源并创建项目（调用项目管理模块）"""
        try:
            # 基础参数提取（保留视图层的请求解析职责）
            map_id = request.data.get('map_id')
            layer_ids = request.data.get('layer_ids')
            task_modes = request.data.get('task_modes', [])
            
            project = create_project(map_id, layer_ids, task_modes)  # 调用独立模块

            # 新增：保存 node 和 edge 逻辑
            nodes_data = request.data.get('nodes', [])
            edges_data = request.data.get('edges', [])

            # 保存 nodes（假设每个 node 需关联到 project 或 layer，示例关联到 project）
            created_nodes = []
            for node_data in nodes_data:
                # 补充必要关联字段（根据实际模型字段调整）
                node_data['project'] = project.id
                node = Node.objects.create(**node_data)
                created_nodes.append(node.id)

            # 保存 edges（需关联源节点和目标节点）
            created_edges = []
            for edge_data in edges_data:
                source_node_id = edge_data.get('source_node')
                target_node_id = edge_data.get('target_node')
                if not source_node_id or not target_node_id:
                    raise ValidationError("边数据缺少源节点或目标节点ID")
                
                # 校验节点是否存在
                if not Node.objects.filter(id=source_node_id).exists():
                    raise ValidationError(f"源节点 {source_node_id} 不存在")
                if not Node.objects.filter(id=target_node_id).exists():
                    raise ValidationError(f"目标节点 {target_node_id} 不存在")
                
                # 补充必要关联字段（根据实际模型字段调整）
                edge_data['project'] = project.id
                edge = Edge.objects.create(**edge_data)
                created_edges.append(edge.id)

            # 关联map和layers到项目
            project.map = Map.objects.get(id=map_id)
            project.layers.set(Layer.objects.filter(id__in=layer_ids))
            project.save()  # 保存关联关系
            
            tasks.generate_topology_and_config.delay(project.id)  # 保留异步任务调用
            
            return Response({
                'project_id': project.id, 
                'status': 'pending',
                'created_nodes': created_nodes,
                'created_edges': created_edges
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Map.DoesNotExist:
            return Response({'error': '指定的Map不存在'}, status=status.HTTP_400_BAD_REQUEST)
        except Layer.DoesNotExist:
            return Response({'error': '指定的Layer不存在'}, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='single-target')
    # def single_target_input(self, request):
    def single_target_input(self, request, pk):
        # pk = 123  # 假设 pk 是项目ID
        print(pk)
        """单点模式目标输入（通过rabbitmq发送）"""
        target_data = request.data.get('target')
        # project = get_object_or_404(Project, id=pk)
        project_id = int(pk)
        # if 'single_point' not in project.task_modes:
        #     return Response({'error': '非单点模式项目'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 发送到rabbitmq（示例使用celery发送）
        # tasks.send_target_to_rabbitmq.delay(project.id, target_data)
        # 示例：假设 target_data 包含 datetime 对象，需转换为字符串
        from django.utils import timezone
        target_data = {
            "time": timezone.now().isoformat(),  # datetime → 字符串
            "node": request.data.get('target')
        }
        from .rabbitmq import send_to_rabbitmq
        send_to_rabbitmq(project_id, target_data)

        # tasks.send_target_to_rabbitmq.apply_async(args=[project_id, target_data], queue='default')
        return Response({'message': '目标已发送'})

    @action(detail=True, methods=['post'], url_path='brute-force-area')
    def brute_force_area_input(self, request, pk):
        """暴力计算区域输入"""
        area_json = request.data.get('area')
        project = get_object_or_404(Project, id=pk)
        
        if 'brute_force' not in project.task_modes:
            return Response({'error': '非暴力计算模式项目'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 异步计算组合
        tasks.calculate_brute_force_combinations.delay(project.id, area_json)
        return Response({'message': '区域数据已接收'})

class LatestResourcesAPIView(APIView):
    """获取最新的map和layer资源"""
    def get(self, request):
        try:
            # 调用resource_client中的方法获取最新资源
            latest_resources = resource_client.get_latest_resources_from_admin()
            return Response(latest_resources, status=status.HTTP_200_OK)
        except ValueError as e:
            # 捕获resource_client可能抛出的异常并返回错误信息
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], url_path='get-layer-nodes')
    def get_layer_nodes(self, request, pk):
        """
        输入示例: {"layers": ["电力图层", "燃气图层"]}
        输出示例: {"node": [{"id": 1, "name": "变电站A", "type": "002", "options": {"电压": "110kV"}}, ...]}
        """
        try:
            # 1. 校验输入参数
            layer_names = request.data.get('layers')
            if not layer_names or not isinstance(layer_names, list):
                return Response({"error": "输入需包含'layers'字段且为列表类型"}, status=status.HTTP_400_BAD_REQUEST)

            # 2. 获取 project 及其关联的 map
            # project = get_object_or_404(Project, id=pk)
            project_map = project.map  # 假设 Project 通过 map 字段关联 Map 模型

            # 3. 从 map 中筛选指定名称的 layer
            target_layers = Layer.objects.filter(
                map=project_map,  # 关联当前 project 的 map
                name__in=layer_names  # 名称在输入列表中
            )

            # 4. 收集所有 layer 下的 node 信息（合并到 node 键的列表）
            node_list = []
            for layer in target_layers:
                nodes = layer.nodes.all()  # 假设 Layer 通过 nodes 字段关联 Node 模型
                for node in nodes:
                    node_info = {
                        "id": node.id,
                        "name": node.name,
                        "type": node.type,
                        "options": node.options  # 假设 options 是 JSONField 或字典
                    }
                    node_list.append(node_info)

            # 5. 构造输出（符合用户要求的 {node: [...]} 格式）
            return Response({"node": node_list}, status=status.HTTP_200_OK)

        except Project.DoesNotExist:
            return Response({"error": "项目不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"服务器内部错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class InfluxDataAPIView(APIView):
    def get(self, request):
        """
        GET接口：获取InfluxDB数据（支持id参数）
        示例请求：business-flow/influx-data/?id=your_id
        """
        # 从查询参数获取id（默认abc）
        target_id = request.query_params.get('id', 'abc')
        # 调用InfluxDB查询函数
        data = query_influxdb_data(target_id)
        return Response(
            {"code": 200, "message": "查询成功", "data": data},
            status=status.HTTP_200_OK
        )


# 1. 添加模板API（自动关联最新Project的map和technique）
class CreateTemplateAPI(APIView):
    def post(self, request):
        # 验证必填字段
        serializer = TemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 获取最新项目（可能不存在）
        project = None
        message = ''
        try:
            project = Project.objects.latest('created_at')
        except Project.DoesNotExist:
            message = 'Current no latest Project record'

        # 创建模板（即使project为None也保存基础信息）
        template = Template(
            name=serializer.validated_data['name'],
            description=serializer.validated_data['description'],
            map=project.map if project else None,
            technique=project.technique if project else None
        )
        template.save()

        # 返回包含提示信息的响应
        return Response({
            'id': template.id,
            'message': message,
            'data': TemplateSerializer(template).data
        }, status=status.HTTP_201_CREATED)

# 2. 查看所有模板API
class ListTemplatesAPI(generics.ListAPIView):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

# 3. 查看指定模板的map节点信息API
class RetrieveTemplateNodesAPI(generics.RetrieveAPIView):
    queryset = Template.objects.all()
    serializer_class = TemplateSerializer

    def retrieve(self, request, *args, **kwargs):
        template = self.get_object()
        map_id = template.map_info.get('id')  # 从模板中获取map的ID
        try:
            map_obj = Map.objects.get(id=map_id)
        except Map.DoesNotExist:
            raise NotFound('模板关联的Map不存在')

        # 获取Map下的所有Layer及节点（格式：{layer: {node: ...}}）
        layers = map_obj.map_layers.all()  # 假设Map通过map_layers关联MapLayer
        result = {}
        for map_layer in layers:
            layer = map_layer.layer
            nodes = Node.objects.filter(layer=layer)
            node_data = TemplateNodeSerializer(nodes, many=True).data
            result[layer.type] = {'nodes': node_data}  # 假设layer.type是图层类型

        return Response(result)

# 将新视图添加到BusinessFlowViewSet或独立注册（根据项目路由风格）