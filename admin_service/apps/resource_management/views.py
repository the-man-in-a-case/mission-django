from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import ResourceImportJob
from .serializers import ResourceImportJobSerializer
from resourcedb.models import Layer, Map, Node, BaseNode, BaseEdge, Map_Layer  # 补充BaseEdge导入

class ResourceImportJobViewSet(viewsets.ModelViewSet):
    queryset = ResourceImportJob.objects.all()
    serializer_class = ResourceImportJobSerializer

    def perform_create(self, serializer):
        job = serializer.save(status='running')
        self.execute_import_job(job)
        return job

    def execute_import_job(self, job):
        """仅保留外部API导入逻辑"""
        try:
            if job.import_type == 'layer':
                if not job.api_data:
                    job.status = 'failed'
                    job.log += "错误：未提供外部API数据\n"
                    job.save()
                    return

                # 校验外部数据格式
                required_fields = ['type', 'version_number', 'author', 'message']
                if not all(field in job.api_data for field in required_fields):
                    raise ValidationError('外部API数据缺少必要字段（type/version_number/author/message）')

                # 创建新Layer
                layer = Layer.objects.create(
                    type=job.api_data['type'],
                    version_number=job.api_data['version_number'],
                    author=job.api_data['author'],
                    message=job.api_data['message']
                )
                job.target_id = layer.id
                job.log += f"成功通过API创建Layer（ID={layer.id}）\n"

                # 级联创建Node
                nodes_data = job.api_data.get('nodes', [])
                for node_data in nodes_data:
                    base_node = BaseNode.objects.create(**node_data)
                    Node.objects.create(layer=layer, base_node=base_node)
                job.log += f"成功导入{len(nodes_data)}个节点\n"
                job.status = 'success'

            elif job.import_type == 'map':
                if not job.api_data:
                    job.status = 'failed'
                    job.log += "错误：未提供外部API数据\n"
                    job.save()
                    return

                # 校验Map数据格式
                required_fields = ['version_number']
                if not all(field in job.api_data for field in required_fields):
                    raise ValidationError('外部API数据缺少必要字段（version_number）')

                # 创建新Map
                map_obj = Map.objects.create(
                    version_number=job.api_data['version_number']
                )
                job.target_id = map_obj.id
                job.log += f"成功通过API创建Map（ID={map_obj.id}）\n"

                # 级联创建关联的Layer
                layers_data = job.api_data.get('layers', [])
                for layer_data in layers_data:
                    layer = Layer.objects.create(
                        type=layer_data['type'],
                        version_number=layer_data['version_number'],
                        author=layer_data['author'],
                        message=layer_data['message']
                    )
                    Map_Layer.objects.create(MapID=map_obj, LayerID=layer)
                    job.log += f"成功关联Layer（ID={layer.id}）到Map\n"
                job.status = 'success'

            elif job.import_type == 'base_node':  # 新增BaseNode批量添加
                if not job.api_data:
                    job.status = 'failed'
                    job.log += "错误：未提供BaseNode外部API数据\n"
                    job.save()
                    return

                # 校验BaseNode数据格式（示例必要字段）
                required_fields = ['base_node_name', 'cis_type', 'sub_type']
                for idx, node_data in enumerate(job.api_data, 1):
                    if not all(field in node_data for field in required_fields):
                        raise ValidationError(f'第{idx}个BaseNode数据缺少必要字段（base_node_name/cis_type/sub_type）')

                # 批量创建BaseNode
                created_count = 0
                for node_data in job.api_data:
                    BaseNode.objects.create(**node_data)
                    created_count += 1
                job.target_id = None  # 批量操作无单一目标ID
                job.log += f"成功批量创建{created_count}个BaseNode\n"
                job.status = 'success'

            elif job.import_type == 'base_edge':  # 新增BaseEdge批量添加
                if not job.api_data:
                    job.status = 'failed'
                    job.log += "错误：未提供BaseEdge外部API数据\n"
                    job.save()
                    return

                # 校验BaseEdge数据格式（示例必要字段）
                required_fields = ['base_edge_name']
                for idx, edge_data in enumerate(job.api_data, 1):
                    if not all(field in edge_data for field in required_fields):
                        raise ValidationError(f'第{idx}个BaseEdge数据缺少必要字段（base_edge_name）')

                # 批量创建BaseEdge
                created_count = 0
                for edge_data in job.api_data:
                    BaseEdge.objects.create(**edge_data)
                    created_count += 1
                job.target_id = None  # 批量操作无单一目标ID
                job.log += f"成功批量创建{created_count}个BaseEdge\n"
                job.status = 'success'

            else:
                job.status = 'failed'
                job.log += "未知的导入类型\n"

        except Exception as e:
            job.status = 'failed'
            job.log += f"导入失败：{str(e)}\n"
        
        job.save()

# 新增：导出Map和Layer的API视图
from rest_framework import generics
from resourcedb.serializers import MapExportSerializer, LayerExportSerializer  # 确保导入正确

class MapExportAPIView(generics.RetrieveAPIView):
    queryset = Map.objects.all()
    serializer_class = MapExportSerializer  # 使用包含关联数据的序列化器
    lookup_field = 'id'

class LayerExportAPIView(generics.RetrieveAPIView):
    queryset = Layer.objects.all()
    serializer_class = LayerExportSerializer  # 使用包含关联数据的序列化器
    lookup_field = 'id'

class MapListAPIView(generics.ListAPIView):
    """查看所有Map"""
    queryset = Map.objects.all()
    serializer_class = MapExportSerializer

class LayerListAPIView(generics.ListAPIView):
    """查看所有Layer"""
    queryset = Layer.objects.all()
    serializer_class = LayerExportSerializer


class LatestMapExportAPIView(generics.RetrieveAPIView):
    """导出最新创建的Map为JSON"""
    queryset = Map.objects.all()
    serializer_class = MapExportSerializer

    def get_object(self):
        # 按创建时间降序取第一条（最新）
        latest_map = Map.objects.order_by('-created_at').first()
        if not latest_map:
            raise ValidationError("当前没有已创建的Map数据")
        return latest_map

class LatestLayerExportAPIView(generics.RetrieveAPIView):
    """导出最新创建的Layer为JSON"""
    queryset = Layer.objects.all()
    serializer_class = LayerExportSerializer

    def get_object(self):
        # 按创建时间降序取第一条（最新）
        latest_layer = Layer.objects.order_by('-created_at').first()
        if not latest_layer:
            raise ValidationError("当前没有已创建的Layer数据")
        return latest_layer