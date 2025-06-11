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
        if value not in ['map', 'layer']:
            raise serializers.ValidationError("无效的导入类型，仅支持'map'或'layer'")
        return value

    def validate_target_id(self, value):
        # 外部导入时target_id由系统生成，无需提前验证存在性
        return value

    def validate(self, attrs):
        import_type = attrs.get('import_type')
        api_data = attrs.get('api_data')
        
        # 补充特定类型的字段校验
        if import_type == 'layer':
            required = ['type', 'version_number', 'author', 'message']
            if not all(k in api_data for k in required):
                raise serializers.ValidationError("layer类型API数据需包含type/version_number/author/message")
        elif import_type == 'map':
            if 'version_number' not in api_data:
                raise serializers.ValidationError("map类型API数据需包含version_number")
        
        return attrs