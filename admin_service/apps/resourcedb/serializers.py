from rest_framework import serializers
from .models import Map, Layer, Node, Edge, IntraEdge, BaseNode, BaseEdge

# 基础节点序列化器（用于展示节点核心信息）
class BaseNodeSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseNode
        fields = ['id', 'base_node_name', 'cis_type', 'sub_type']

# 基础边序列化器（用于展示边核心信息）
class BaseEdgeSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseEdge
        fields = ['id', 'base_edge_name']

# 节点序列化器（关联基础节点）
class NodeSerializer(serializers.ModelSerializer):
    base_node = BaseNodeSimpleSerializer()  # 嵌套基础节点信息

    class Meta:
        model = Node
        fields = ['id', 'base_node']

# 边序列化器（关联基础边）
class EdgeSerializer(serializers.ModelSerializer):
    base_edge = BaseEdgeSimpleSerializer()  # 嵌套基础边信息

    class Meta:
        model = Edge
        fields = ['id', 'base_edge']

# 图层导出序列化器（包含关联节点和边）
class LayerExportSerializer(serializers.ModelSerializer):
    nodes = NodeSerializer(source='node_set', many=True)  # 通过反向关联获取图层下的所有节点
    edges = serializers.SerializerMethodField()  # 自定义边获取逻辑

    class Meta:
        model = Layer
        fields = ['id', 'type', 'version_number', 'author', 'message', 'nodes', 'edges']

    def get_edges(self, obj):
        """通过IntraEdge获取图层关联的边"""
        intra_edges = IntraEdge.objects.filter(layer=obj)
        edges = [ie.edge for ie in intra_edges]
        return EdgeSerializer(edges, many=True).data

# 地图导出序列化器（包含关联图层）
class MapExportSerializer(serializers.ModelSerializer):
    layers = LayerExportSerializer(source='map_layers.layer', many=True)  # 通过MapLayer获取关联图层

    class Meta:
        model = Map
        fields = ['id', 'version_number', 'author', 'message', 'layers']