from django.contrib import admin
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    BaseNode, BaseEdge, Map, Layer, MapLayer, Node, MechanismRelationship,
    Edge, IntraEdge, Configuration, Technique, TargetNode, Diagram,
    Condition, Record, Execution, AnalysisAlgorithm, FormatConversion,
    Result, Simulation, Project
)
from .models import ResourceImportJob  # 需在顶部导入新增模型


# 自定义表单验证
class BaseNodeAdminForm(ModelForm):
    class Meta:
        model = BaseNode
        fields = '__all__'
    
    def clean_attribute(self):
        attribute = self.cleaned_data.get('attribute')
        if attribute:
            try:
                if isinstance(attribute, str):
                    json.loads(attribute)
            except (json.JSONDecodeError, TypeError):
                raise ValidationError('Invalid JSON format for attribute field')
        return attribute

    def clean(self):
        cleaned_data = super().clean()
        cis_type = cleaned_data.get('cis_type')
        sub_type = cleaned_data.get('sub_type')
        
        # 根据CIS类型验证子类型的合理性
        if cis_type and sub_type:
            cis_subtype_mapping = {
                '001': ['1-1Terminal', '1-2Bearer'],  # 通信系统
                '002': ['2-1Gen', '2-2Trans', '2-3Dis', '2-4Load'],  # 电力系统
                '003': ['3-1GasExploit', '3-2GasTrans', '3-3GasLoad'],  # 燃气系统
                '004': ['4-1Draw', '4-2Gen', '4-3Trans', '4-4Dis', '4-5SecondSup', '4-6Load'],  # 供水系统
            }
            
            valid_subtypes = cis_subtype_mapping.get(cis_type, [])
            if valid_subtypes and sub_type not in valid_subtypes:
                raise ValidationError(f'Sub type {sub_type} is not valid for CIS type {cis_type}')
        
        return cleaned_data


class EdgeAdminForm(ModelForm):
    class Meta:
        model = Edge
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        source_node = cleaned_data.get('source_node')
        destination_node = cleaned_data.get('destination_node')
        
        if source_node and destination_node:
            if source_node.id == destination_node.id:
                raise ValidationError('Source and destination nodes cannot be the same')
            
            # 检查节点类型兼容性
            if source_node.cis_type and destination_node.cis_type:
                if source_node.cis_type == destination_node.cis_type:
                    # 同类型系统内部连接通常是合理的
                    pass
                else:
                    # 不同类型系统间的连接需要特别验证
                    incompatible_pairs = [
                        ('001', '003'),  # 通信系统不应直接连燃气系统
                    ]
                    if (source_node.cis_type, destination_node.cis_type) in incompatible_pairs:
                        raise ValidationError(
                            f'Connection between {source_node.cis_type} and {destination_node.cis_type} '
                            f'systems may not be appropriate'
                        )
        
        return cleaned_data


class RecordAdminForm(ModelForm):
    class Meta:
        model = Record
        fields = '__all__'
    
    def clean_record_data(self):
        record_data = self.cleaned_data.get('record_data')
        if record_data:
            try:
                if isinstance(record_data, str):
                    json.loads(record_data)
            except (json.JSONDecodeError, TypeError):
                raise ValidationError('Invalid JSON format for record_data field')
        return record_data


# 内联管理器
class NodeInline(admin.TabularInline):
    model = Node
    extra = 0
    raw_id_fields = ('base_node',)
    verbose_name = "层内节点"
    verbose_name_plural = "层内节点"


class IntraEdgeInline(admin.TabularInline):
    model = IntraEdge
    extra = 0
    raw_id_fields = ('edge',)
    verbose_name = "层内边"
    verbose_name_plural = "层内边"


class MapLayerInline(admin.TabularInline):
    model = MapLayer
    extra = 0
    verbose_name = "地图图层"
    verbose_name_plural = "地图图层"


class TargetNodeInline(admin.TabularInline):
    model = TargetNode
    extra = 0
    raw_id_fields = ('node',)
    verbose_name = "目标节点"
    verbose_name_plural = "目标节点"


# 主要管理器类
@admin.register(BaseNode)
class BaseNodeAdmin(admin.ModelAdmin):
    form = BaseNodeAdminForm
    list_display = [
        'id', 'base_node_name', 'cis_type', 'sub_type', 
        'nation', 'province', 'city', 'model_name', 'owner'
    ]
    list_filter = ['cis_type', 'sub_type', 'nation', 'province', 'city', 'owner']
    search_fields = [
        'base_node_name', 'base_node_desc', 'model_name', 
        'nation', 'province', 'city', 'owner'
    ]
    fieldsets = (
        ('基本信息', {
            'fields': ('base_node_name', 'base_node_desc', 'model_name', 'owner')
        }),
        ('分类信息', {
            'fields': ('cis_type', 'sub_type', 'coverage')
        }),
        ('地理位置', {
            'fields': (
                'geo_location', 'nation', 'province', 'city', 
                'district', 'street', 'no', 'location'
            ),
            'classes': ('collapse',)
        }),
        ('扩展属性', {
            'fields': ('attribute',),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('id',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related()


@admin.register(BaseEdge)
class BaseEdgeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'base_edge_name', 'nation', 'province', 'city'
    ]
    list_filter = ['nation', 'province', 'city']
    search_fields = ['base_edge_name', 'base_edge_desc']
    fieldsets = (
        ('基本信息', {
            'fields': ('base_edge_name', 'base_edge_desc')
        }),
        ('地理位置', {
            'fields': (
                'geo_location', 'nation', 'province', 'city', 
                'district', 'street', 'no', 'location'
            ),
            'classes': ('collapse',)
        }),
        ('扩展属性', {
            'fields': ('attribute',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Map)
class MapAdmin(admin.ModelAdmin):
    list_display = ['id', 'version_number', 'author', 'layer_count', 'created_info']
    inlines = [MapLayerInline]
    list_filter = ['version_number', 'author']
    search_fields = ['message']
    
    def layer_count(self, obj):
        return obj.map_layers.count()
    layer_count.short_description = '图层数量'
    
    def created_info(self, obj):
        return f"Map-{obj.id} (v{obj.version_number})"
    created_info.short_description = '地图信息'

    fieldsets = (
        ('基本信息', {
            'fields': ('version_number', 'author', 'message')
        }),
        ('版本控制', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('id', 'created_at', 'updated_at')


@admin.register(Layer)
class LayerAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'version_number', 'author', 'create_time', 'node_count', 'edge_count']
    list_filter = ['type', 'version_number', 'author', 'create_time']
    search_fields = ['type', 'message']
    inlines = [NodeInline, IntraEdgeInline]
    readonly_fields = ('create_time', 'created_at', 'updated_at')

    fieldsets = (
        ('基本信息', {
            'fields': ('type', 'version_number', 'author', 'message')
        }),
        ('时间信息', {
            'fields': ('create_time', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def node_count(self, obj):
        return obj.nodes.count()
    node_count.short_description = '节点数量'
    
    def edge_count(self, obj):
        return obj.intra_edges.count()
    edge_count.short_description = '边数量'


@admin.register(MapLayer)
class MapLayerAdmin(admin.ModelAdmin):
    list_display = ['id', 'map', 'layer', 'layer_type']
    list_filter = ['layer__type']
    raw_id_fields = ('map', 'layer')
    
    def layer_type(self, obj):
        return obj.layer.get_type_display() if obj.layer else '-'
    layer_type.short_description = '图层类型'


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ['id', 'layer', 'base_node', 'node_name', 'node_type']
    list_filter = ['layer__type', 'base_node__cis_type', 'base_node__sub_type']
    search_fields = ['base_node__base_node_name']
    raw_id_fields = ('layer', 'base_node')
    
    def node_name(self, obj):
        return obj.base_node.base_node_name if obj.base_node else '-'
    node_name.short_description = '节点名称'
    
    def node_type(self, obj):
        return obj.base_node.get_cis_type_display() if obj.base_node else '-'
    node_type.short_description = '节点类型'


@admin.register(MechanismRelationship)
class MechanismRelationshipAdmin(admin.ModelAdmin):
    list_display = ['id', 'business_summary', 'function_summary']
    search_fields = ['business', 'function', 'composition', 'behavior', 'state']
    
    def business_summary(self, obj):
        return (obj.business[:50] + '...') if obj.business and len(obj.business) > 50 else obj.business or '-'
    business_summary.short_description = '业务关系'
    
    def function_summary(self, obj):
        return (obj.function[:50] + '...') if obj.function and len(obj.function) > 50 else obj.function or '-'
    function_summary.short_description = '功能'


@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    form = EdgeAdminForm
    list_display = [
        'base_edge_id', 'source_node', 'destination_node', 
        'relationship_summary', 'edge_visualization'
    ]
    list_filter = [
        'source_node__cis_type', 'destination_node__cis_type',
        'source_node__nation', 'source_node__province'
    ]
    search_fields = [
        'source_node__base_node_name', 'destination_node__base_node_name',
        'base_edge__base_edge_name'
    ]
    raw_id_fields = ('base_edge', 'source_node', 'destination_node', 'mechanism_relationship')
    
    def relationship_summary(self, obj):
        if obj.mechanism_relationship and obj.mechanism_relationship.business:
            business = obj.mechanism_relationship.business
            return (business[:30] + '...') if len(business) > 30 else business
        return '-'
    relationship_summary.short_description = '关系描述'
    
    def edge_visualization(self, obj):
        return format_html(
            '<span style="color: #007cba;">{}</span> → <span style="color: #e74c3c;">{}</span>',
            obj.source_node.base_node_name or f'Node-{obj.source_node_id}',
            obj.destination_node.base_node_name or f'Node-{obj.destination_node_id}'
        )
    edge_visualization.short_description = '连接关系'


@admin.register(IntraEdge)
class IntraEdgeAdmin(admin.ModelAdmin):
    list_display = ['id', 'layer', 'edge', 'edge_info']
    list_filter = ['layer__type']
    raw_id_fields = ('layer', 'edge')
    
    def edge_info(self, obj):
        if obj.edge:
            return f"{obj.edge.source_node_id} → {obj.edge.destination_node_id}"
        return '-'
    edge_info.short_description = '边信息'


@admin.register(Configuration)
class ConfigurationAdmin(admin.ModelAdmin):
    list_display = ['id', 'layer', 'layer_type', 'related_items']
    list_filter = ['layer__type']
    raw_id_fields = ('layer',)
    
    def layer_type(self, obj):
        return obj.layer.get_type_display() if obj.layer else '-'
    layer_type.short_description = '图层类型'
    
    def related_items(self, obj):
        if obj.layer:
            node_count = obj.layer.nodes.count()
            edge_count = obj.layer.intra_edges.count()
            return f"{node_count} 节点, {edge_count} 边"
        return '-'
    related_items.short_description = '关联项目'


@admin.register(Technique)
class TechniqueAdmin(admin.ModelAdmin):
    list_display = ['id', 'type', 'target_node_count']
    list_filter = ['type']
    inlines = [TargetNodeInline]
    
    def target_node_count(self, obj):
        return obj.target_nodes.count()
    target_node_count.short_description = '目标节点数'


@admin.register(TargetNode)
class TargetNodeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'technique', 'node', 'target_sequence', 
        'target_effect', 'node_info'
    ]
    list_filter = ['technique__type', 'node__cis_type']
    search_fields = ['node__base_node_name']
    raw_id_fields = ('technique', 'node')
    
    def node_info(self, obj):
        if obj.node:
            return f"{obj.node.base_node_name or f'Node-{obj.node_id}'} ({obj.node.get_cis_type_display()})"
        return '-'
    node_info.short_description = '节点信息'


@admin.register(Diagram)
class DiagramAdmin(admin.ModelAdmin):
    list_display = ['id', 'map', 'configuration', 'technique', 'summary']
    list_filter = ['technique__type', 'configuration__layer__type']
    raw_id_fields = ('map', 'configuration', 'technique')
    
    def summary(self, obj):
        return f"Map-{obj.map_id}, Config-{obj.configuration_id}, Tech-{obj.technique_id}"
    summary.short_description = '摘要'


@admin.register(Condition)
class ConditionAdmin(admin.ModelAdmin):
    list_display = ['id', 'status', 'simulation_count']
    list_filter = ['status']
    
    def simulation_count(self, obj):
        return obj.simulations.count()
    simulation_count.short_description = '仿真数量'


@admin.register(Record)
class RecordAdmin(admin.ModelAdmin):
    form = RecordAdminForm
    list_display = ['id', 'data_summary', 'execution_count']
    search_fields = ['record_data']
    
    def data_summary(self, obj):
        if obj.record_data:
            try:
                data_str = str(obj.record_data)
                return (data_str[:50] + '...') if len(data_str) > 50 else data_str
            except:
                return 'JSON Data'
        return '-'
    data_summary.short_description = '数据摘要'
    
    def execution_count(self, obj):
        return obj.executions.count()
    execution_count.short_description = '执行次数'


@admin.register(Execution)
class ExecutionAdmin(admin.ModelAdmin):
    list_display = ['id', 'iteration', 'record', 'simulation_count']
    list_filter = ['iteration']
    raw_id_fields = ('record',)
    
    def simulation_count(self, obj):
        return obj.simulations.count()
    simulation_count.short_description = '仿真数量'


@admin.register(AnalysisAlgorithm)
class AnalysisAlgorithmAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'parameters_summary', 'result_count']
    search_fields = ['name', 'parameters']
    
    def parameters_summary(self, obj):
        if obj.parameters:
            return (obj.parameters[:50] + '...') if len(obj.parameters) > 50 else obj.parameters
        return '-'
    parameters_summary.short_description = '参数摘要'
    
    def result_count(self, obj):
        return obj.results.count()
    result_count.short_description = '结果数量'


@admin.register(FormatConversion)
class FormatConversionAdmin(admin.ModelAdmin):
    list_display = ['id', 'input_format', 'output_format', 'conversion_info']
    list_filter = ['input_format', 'output_format']
    search_fields = ['input_format', 'output_format']
    
    def conversion_info(self, obj):
        return f"{obj.input_format or 'Unknown'} → {obj.output_format or 'Unknown'}"
    conversion_info.short_description = '转换信息'


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'analysis_algorithm', 'format_conversion', 'simulation_count']
    list_filter = [
        'analysis_algorithm__name', 
        'format_conversion__input_format',
        'format_conversion__output_format'
    ]
    raw_id_fields = ('analysis_algorithm', 'format_conversion')
    
    def simulation_count(self, obj):
        return obj.simulations.count()
    simulation_count.short_description = '仿真数量'


@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'condition', 'execution', 'result', 
        'status_info', 'project_count'
    ]
    list_filter = ['condition__status', 'execution__iteration']
    raw_id_fields = ('condition', 'execution', 'result')
    
    def status_info(self, obj):
        return obj.condition.get_status_display() if obj.condition else '-'
    status_info.short_description = '状态'
    
    def project_count(self, obj):
        return obj.projects.count()
    project_count.short_description = '项目数量'


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['id', 'diagram', 'simulation', 'project_summary']
    raw_id_fields = ('diagram', 'simulation')
    
    def project_summary(self, obj):
        status = obj.simulation.condition.get_status_display() if obj.simulation and obj.simulation.condition else 'Unknown'
        return f"Diagram-{obj.diagram_id}, Status: {status}"
    project_summary.short_description = '项目摘要'


# 自定义Admin站点标题
admin.site.site_header = "资源管理系统"
admin.site.site_title = "资源管理系统管理"
admin.site.index_title = "系统管理"


@admin.register(ResourceImportJob)
class ResourceImportJobAdmin(admin.ModelAdmin):
    list_display = ['id', 'import_type', 'status', 'created_at', 'completed_at']  # Removed 'updated_at' and 'imported_by'
    list_filter = ['status', 'import_type', 'created_at']
    search_fields = ['imported_data']
    readonly_fields = ['created_at', 'completed_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('file_path', 'imported_by')
        }),
        ('状态信息', {
            'fields': ('status', 'progress', 'error_message')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )