from rest_framework import serializers
from ..resourcedb.models import Template, BaseNode  # 假设Template模型已定义

class TemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Template
        fields = ['id', 'name', 'description', 'map_info', 'technique_info']  # 假设字段
        extra_kwargs = {
            'name': {'required': True, 'allow_blank': False},  # 名字必填且非空
            'description': {'required': True, 'allow_blank': False},  # 描述必填且非空
            'map_info': {'required': False, 'allow_null': True},  # 其他字段可选
            'technique_info': {'required': False, 'allow_null': True}
        }
class TemplateNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BaseNode
        fields = ['id', 'base_node', 'attribute']  # 根据实际Node模型字段调整