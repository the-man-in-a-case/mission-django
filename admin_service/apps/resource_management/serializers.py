from rest_framework import serializers
from .models import ResourceImportJob
from resourcedb.models import Layer, Map

class ResourceImportJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResourceImportJob
        fields = '__all__'
        read_only_fields = ('status', 'log', 'created_at', 'updated_at')
        extra_kwargs = {
            'api_data': {'required': True}  # 强制要求提供外部API数据
        }

    def validate_import_type(self, value):
        # 新增支持 base_node 和 base_edge 导入类型
        if value not in ['map', 'layer', 'base_node', 'base_edge']:
            raise serializers.ValidationError("无效的导入类型，仅支持'map'/'layer'/'base_node'/'base_edge'")
        return value

    def validate_target_id(self, value):
        # 外部导入时target_id由系统生成，无需提前验证存在性
        return value

    def validate(self, attrs):
        import_type = attrs.get('import_type')
        api_data = attrs.get('api_data')

        # 补充所有类型的字段校验逻辑
        if import_type == 'layer':
            required = ['type', 'version_number', 'author', 'message']
            if not all(k in api_data for k in required):
                raise serializers.ValidationError("layer类型API数据需包含type/version_number/author/message")
        elif import_type == 'map':
            if 'version_number' not in api_data:
                raise serializers.ValidationError("map类型API数据需包含version_number")
        elif import_type == 'base_node':
            required = ['base_node_name', 'cis_type', 'sub_type']
            if not all(k in api_data[0] for k in required):  # 假设api_data是列表
                raise serializers.ValidationError("base_node类型API数据需包含base_node_name/cis_type/sub_type")
        elif import_type == 'base_edge':
            required = ['base_edge_name']
            if not all(k in api_data[0] for k in required):  # 假设api_data是列表
                raise serializers.ValidationError("base_edge类型API数据需包含base_edge_name")

        return attrs