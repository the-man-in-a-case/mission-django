from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import json


class BaseNode(models.Model):
    """节点基类表"""
    
    CIS_TYPE_CHOICES = [
        ('001', '001'),
        ('002', '002'),
        ('003', '003'),
        ('004', '004'),
        ('005', '005'),
        ('006', '006'),
    ]
    
    SUB_TYPE_CHOICES = [
        ('1-1Terminal', '1-1Terminal'),
        ('1-2Bearer', '1-2Bearer'),
        ('2-1Gen', '2-1Gen'),
        ('2-2Trans', '2-2Trans'),
        ('2-3Dis', '2-3Dis'),
        ('2-4Load', '2-4Load'),
        ('3-1GasExploit', '3-1GasExploit'),
        ('3-2GasTrans', '3-2GasTrans'),
        ('3-3GasLoad', '3-3GasLoad'),
        ('4-1Draw', '4-1Draw'),
        ('4-2Gen', '4-2Gen'),
        ('4-3Trans', '4-3Trans'),
        ('4-4Dis', '4-4Dis'),
        ('4-5SecondSup', '4-5SecondSup'),
        ('4-6Load', '4-6Load'),
    ]
    
    base_node_name = models.CharField(max_length=50, null=True, blank=True)
    base_node_desc = models.CharField(max_length=255, null=True, blank=True)
    geo_location = models.CharField(max_length=255, null=True, blank=True)
    nation = models.CharField(max_length=50, null=True, blank=True)
    province = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    district = models.CharField(max_length=50, null=True, blank=True)
    street = models.CharField(max_length=50, null=True, blank=True)
    no = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=50, null=True, blank=True)
    attribute = models.JSONField(null=True, blank=True)
    cis_type = models.CharField(max_length=3, choices=CIS_TYPE_CHOICES, null=True, blank=True)
    sub_type = models.CharField(max_length=15, choices=SUB_TYPE_CHOICES, null=True, blank=True)
    model_name = models.CharField(max_length=50, null=True, blank=True, help_text='仿真模型的名称')
    coverage = models.CharField(max_length=255, null=True, blank=True, help_text='覆盖区域，与具体的区域表对应')
    owner = models.CharField(max_length=50, null=True, blank=True, help_text='所有者')
    
    class Meta:
        db_table = 'BaseNode'
        verbose_name = '节点基类'
        verbose_name_plural = '节点基类'
    
    def __str__(self):
        return f"{self.base_node_name or f'Node-{self.id}'}"
    
    def clean(self):
        """数据校验"""
        # 原有 JSON 格式验证
        if self.attribute:
            try:
                if isinstance(self.attribute, str):
                    json.loads(self.attribute)
            except json.JSONDecodeError:
                raise ValidationError({'attribute': 'Invalid JSON format'})
        
        # 新增 CIS 类型与子类型关联验证
        cis_subtype_mapping = {
            '001': ['1-1Terminal', '1-2Bearer'],  # 通信系统
            '002': ['2-1Gen', '2-2Trans', '2-3Dis', '2-4Load'],  # 电力系统
            '003': ['3-1GasExploit', '3-2GasTrans', '3-3GasLoad'],  # 燃气系统
            '004': ['4-1Draw', '4-2Gen', '4-3Trans', '4-4Dis', '4-5SecondSup', '4-6Load'],  # 供水系统
        }
        if self.cis_type and self.sub_type:
            valid_subtypes = cis_subtype_mapping.get(self.cis_type, [])
            if valid_subtypes and self.sub_type not in valid_subtypes:
                raise ValidationError({
                    'sub_type': f'子类型 {self.sub_type} 不适用于 CIS 类型 {self.cis_type}'
                })


class BaseEdge(models.Model):
    """边基类表"""
    
    base_edge_name = models.CharField(max_length=50, null=True, blank=True)
    base_edge_desc = models.CharField(max_length=255, null=True, blank=True)
    geo_location = models.CharField(max_length=255, null=True, blank=True)
    nation = models.CharField(max_length=50, null=True, blank=True)
    province = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    district = models.CharField(max_length=50, null=True, blank=True)
    street = models.CharField(max_length=50, null=True, blank=True)
    no = models.CharField(max_length=50, null=True, blank=True)
    location = models.CharField(max_length=50, null=True, blank=True)
    attribute = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'BaseEdge'
        verbose_name = '边基类'
        verbose_name_plural = '边基类'
    
    def __str__(self):
        return f"{self.base_edge_name or f'Edge-{self.id}'}"
    
    def clean(self):
        """数据校验"""
        if self.attribute:
            try:
                if isinstance(self.attribute, str):
                    json.loads(self.attribute)
            except json.JSONDecodeError:
                raise ValidationError({'attribute': 'Invalid JSON format'})
 # 新增节点关联验证（示例）
        if self.source_node and self.destination_node:
            if self.source_node.id == self.destination_node.id:
                raise ValidationError('源节点与目标节点不能相同')
            # 可扩展其他业务规则（如跨系统连接限制）

class Map(models.Model):
    """地图表，一个map由多个Layer组成"""
    version_number = models.PositiveIntegerField(default=1, help_text='版本号')
    author = models.CharField(max_length=50, blank=True, help_text='版本创建者')  # 新增版本创建者
    message = models.TextField(blank=True, help_text='版本提交说明')  
    # commit_hash = models.CharField(max_length=40, blank=True, help_text='Git式提交哈希')
    # parent_version = models.ForeignKey('self', null=True, blank=True, 
    #                                   on_delete=models.SET_NULL, 
    #                                   help_text='父版本')
    # branch = models.CharField(max_length=50, default='main', help_text='分支名称')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    snapshots = models.ManyToManyField('self', symmetrical=False, 
                                        through='MapVersionSnapshot',
                                        related_name='version_snapshots')
    class Meta:
        db_table = 'Map'
        verbose_name = '地图'
        verbose_name_plural = '地图'
    
    def __str__(self):
        return f"Map-{self.id}"


class Layer(models.Model):
    """Layer表，标识Layer的唯一id，并说明Layer的类型"""
    
    LAYER_TYPE_CHOICES = [
        ('FinancialLayer', 'Financial Layer'),
        ('TransportationLayer', 'Transportation Layer'),
        ('WaterLayer', 'Water Layer'),
        ('OilGasLayer', 'Oil Gas Layer'),
        ('TelecommunicationLayer', 'Telecommunication Layer'),
        ('PowerLayer', 'Power Layer'),
        ('EconomicGraphicLayer', 'Economic Graphic Layer'),
        ('demographicLayer', 'Demographic Layer'),
        ('GeographicLayer', 'Geographic Layer'),
        ('MutualLayer', 'Mutual Layer'),
    ]
    
    type = models.CharField(max_length=30, choices=LAYER_TYPE_CHOICES, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True, help_text='图层创建时间')


    version_number = models.PositiveIntegerField(default=1, help_text='版本号')
    # commit_hash = models.CharField(max_length=40, blank=True, help_text='Git式提交哈希')
    # parent_version = models.ForeignKey('self', null=True, blank=True,
    #                                    on_delete=models.SET_NULL,
    #                                    help_text='父版本')
    # branch = models.CharField(max_length=50, default='main', help_text='分支名称')
    author = models.CharField(max_length=50, blank=True, help_text='版本创建者')  # 新增版本创建者
    message = models.TextField(blank=True, help_text='版本提交说明')  # 新增版本说明
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'Layer'
        verbose_name = '图层'
        verbose_name_plural = '图层'
    
    def __str__(self):
        return f"{self.get_type_display() or f'Layer-{self.id}'}"


class MapLayer(models.Model):
    """Map和Layer映射"""
    
    map = models.ForeignKey(
        Map, 
        on_delete=models.RESTRICT, 
        related_name='map_layers',
        help_text='地图ID'
    )
    layer = models.ForeignKey(
        Layer, 
        on_delete=models.RESTRICT, 
        related_name='map_layers',
        help_text='图层ID'
    )
    
    class Meta:
        db_table = 'Map_Layer'
        unique_together = ['map', 'layer']
        verbose_name = '地图图层映射'
        verbose_name_plural = '地图图层映射'
    
    def __str__(self):
        return f"Map {self.map_id} - Layer {self.layer_id}"
    
    def clean(self):
        """数据校验"""
        if self.map_id and not Map.objects.filter(id=self.map_id).exists():
            raise ValidationError({'map': 'Referenced Map does not exist'})
        if self.layer_id and not Layer.objects.filter(id=self.layer_id).exists():
            raise ValidationError({'layer': 'Referenced Layer does not exist'})


class Node(models.Model):
    """Node表，标识每一个Layer中含有的node"""
    
    layer = models.ForeignKey(
        Layer, 
        on_delete=models.RESTRICT, 
        related_name='nodes',
        help_text='图层ID'
    )
    base_node = models.ForeignKey(
        BaseNode, 
        on_delete=models.RESTRICT, 
        related_name='nodes',
        help_text='基础节点ID'
    )
    
    class Meta:
        db_table = 'Node'
        unique_together = ['layer', 'base_node']
        verbose_name = '节点'
        verbose_name_plural = '节点'
    
    def __str__(self):
        return f"Layer {self.layer_id} - Node {self.base_node_id}"
    
    def clean(self):
        """数据校验"""
        if self.layer_id and not Layer.objects.filter(id=self.layer_id).exists():
            raise ValidationError({'layer': 'Referenced Layer does not exist'})
        if self.base_node_id and not BaseNode.objects.filter(id=self.base_node_id).exists():
            raise ValidationError({'base_node': 'Referenced BaseNode does not exist'})


class MechanismRelationship(models.Model):
    """MechanismRelationship表，标识一个边应当具有的业务属性"""
    
    business = models.TextField(null=True, blank=True, help_text='表述业务关系')
    function = models.TextField(null=True, blank=True, help_text='表述功能')
    composition = models.TextField(null=True, blank=True, help_text='表述组成')
    behavior = models.TextField(null=True, blank=True, help_text='表述行为关系')
    state = models.TextField(null=True, blank=True, help_text='表述状态关系')
    
    class Meta:
        db_table = 'MechanismRelationShip'
        verbose_name = '机制关系'
        verbose_name_plural = '机制关系'
    
    def __str__(self):
        return f"MechanismRelationship-{self.id}"


class Edge(models.Model):
    """Edge表，表示边的连接关系"""
    
    # 这里EdgeID引用BaseEdge的ID，但根据SQL结构，我们使用OneToOneField
    base_edge = models.OneToOneField(
        BaseEdge,
        on_delete=models.RESTRICT,
        primary_key=True,
        related_name='edge'
    )
    source_node = models.ForeignKey(
        BaseNode, 
        on_delete=models.RESTRICT, 
        related_name='outgoing_edges',
        help_text='源节点ID'
    )
    mechanism_relationship = models.ForeignKey(
        MechanismRelationship, 
        on_delete=models.RESTRICT, 
        related_name='edges',
        help_text='边业务属性'
    )
    destination_node = models.ForeignKey(
        BaseNode, 
        on_delete=models.RESTRICT, 
        related_name='incoming_edges',
        help_text='目标节点ID'
    )
    
    class Meta:
        db_table = 'Edge'
        verbose_name = '边'
        verbose_name_plural = '边'
    
    def __str__(self):
        return f"Edge: {self.source_node_id} -> {self.destination_node_id}"
    
    def clean(self):
        """数据校验"""
        if self.source_node_id and not BaseNode.objects.filter(id=self.source_node_id).exists():
            raise ValidationError({'source_node': 'Referenced source BaseNode does not exist'})
        if self.destination_node_id and not BaseNode.objects.filter(id=self.destination_node_id).exists():
            raise ValidationError({'destination_node': 'Referenced destination BaseNode does not exist'})
        if self.mechanism_relationship_id and not MechanismRelationship.objects.filter(id=self.mechanism_relationship_id).exists():
            raise ValidationError({'mechanism_relationship': 'Referenced MechanismRelationship does not exist'})
        if self.source_node_id == self.destination_node_id:
            raise ValidationError('Source and destination nodes cannot be the same')


class IntraEdge(models.Model):
    """IntraEdge表，标识每一个Layer中含有的IntraEdge"""
    
    layer = models.ForeignKey(
        Layer, 
        on_delete=models.RESTRICT, 
        related_name='intra_edges',
        help_text='图层ID'
    )
    edge = models.ForeignKey(
        Edge, 
        on_delete=models.RESTRICT, 
        related_name='intra_edges',
        help_text='边ID'
    )
    
    class Meta:
        db_table = 'IntraEdge'
        unique_together = ['layer', 'edge']
        verbose_name = '层内边'
        verbose_name_plural = '层内边'
    
    def __str__(self):
        return f"Layer {self.layer_id} - Edge {self.edge_id}"
    
    def clean(self):
        """数据校验"""
        if self.layer_id and not Layer.objects.filter(id=self.layer_id).exists():
            raise ValidationError({'layer': 'Referenced Layer does not exist'})
        if self.edge_id and not Edge.objects.filter(base_edge_id=self.edge_id).exists():
            raise ValidationError({'edge': 'Referenced Edge does not exist'})


class Configuration(models.Model):
    """配置表，包括配置的图层"""
    
    layer = models.ForeignKey(
        Layer, 
        on_delete=models.RESTRICT, 
        related_name='configurations',
        help_text='图层ID'
    )
    
    class Meta:
        db_table = 'Configuration'
        verbose_name = '配置'
        verbose_name_plural = '配置'
    
    def __str__(self):
        return f"Configuration-{self.id} (Layer: {self.layer_id})"
    
    def clean(self):
        """数据校验"""
        if self.layer_id and not Layer.objects.filter(id=self.layer_id).exists():
            raise ValidationError({'layer': 'Referenced Layer does not exist'})


class Technique(models.Model):
    """JF表，对应特定的JFid和其执行方式"""
    
    TECHNIQUE_TYPE_CHOICES = [
        ('SELECT', 'Select'),
        ('Order', 'Order'),
        ('Random', 'Random'),
    ]
    
    type = models.CharField(max_length=10, choices=TECHNIQUE_TYPE_CHOICES, null=True, blank=True)
    
    class Meta:
        db_table = 'Technique'
        verbose_name = '技术'
        verbose_name_plural = '技术'
    
    def __str__(self):
        return f"Technique-{self.id} ({self.get_type_display()})"


class TargetNode(models.Model):
    """目标节点与JF的对应关系"""
    
    technique = models.ForeignKey(
        Technique, 
        on_delete=models.RESTRICT, 
        related_name='target_nodes',
        help_text='技术ID'
    )
    node = models.ForeignKey(
        BaseNode, 
        on_delete=models.RESTRICT, 
        related_name='target_nodes',
        help_text='目标节点ID'
    )
    target_sequence = models.IntegerField(null=True, blank=True, help_text='执行步序(优先级)')
    target_effect = models.FloatField(null=True, blank=True, help_text='影响效果')
    
    class Meta:
        db_table = 'TargetNode'
        unique_together = ['technique', 'node']
        verbose_name = '目标节点'
        verbose_name_plural = '目标节点'
    
    def __str__(self):
        return f"Technique {self.technique_id} - Node {self.node_id}"
    
    def clean(self):
        """数据校验"""
        if self.technique_id and not Technique.objects.filter(id=self.technique_id).exists():
            raise ValidationError({'technique': 'Referenced Technique does not exist'})
        if self.node_id and not BaseNode.objects.filter(id=self.node_id).exists():
            raise ValidationError({'node': 'Referenced BaseNode does not exist'})
        if self.target_sequence is not None and self.target_sequence < 0:
            raise ValidationError({'target_sequence': 'Target sequence must be non-negative'})


class Diagram(models.Model):
    """图表"""
    
    map = models.ForeignKey(
        Map, 
        on_delete=models.RESTRICT, 
        related_name='diagrams',
        help_text='地图ID'
    )
    configuration = models.ForeignKey(
        Configuration, 
        on_delete=models.RESTRICT, 
        related_name='diagrams',
        help_text='配置ID'
    )
    technique = models.ForeignKey(
        Technique, 
        on_delete=models.RESTRICT, 
        related_name='diagrams',
        help_text='技术ID'
    )
    
    class Meta:
        db_table = 'Diagram'
        verbose_name = '图表'
        verbose_name_plural = '图表'
    
    def __str__(self):
        return f"Diagram-{self.id}"
    
    def clean(self):
        """数据校验"""
        if self.map_id and not Map.objects.filter(id=self.map_id).exists():
            raise ValidationError({'map': 'Referenced Map does not exist'})
        if self.configuration_id and not Configuration.objects.filter(id=self.configuration_id).exists():
            raise ValidationError({'configuration': 'Referenced Configuration does not exist'})
        if self.technique_id and not Technique.objects.filter(id=self.technique_id).exists():
            raise ValidationError({'technique': 'Referenced Technique does not exist'})


class Condition(models.Model):
    """仿真状态表，包括初始、悬停、结束"""
    
    STATUS_CHOICES = [
        ('Initial', 'Initial'),
        ('Suspend', 'Suspend'),
        ('End', 'End'),
    ]
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, null=True, blank=True)
    
    class Meta:
        db_table = 'Conditions'
        verbose_name = '条件'
        verbose_name_plural = '条件'
    
    def __str__(self):
        return f"Condition-{self.id} ({self.get_status_display()})"


class Record(models.Model):
    """记录表"""
    
    record_data = models.JSONField(null=True, blank=True, help_text='记录的内容')
    
    class Meta:
        db_table = 'Record'
        verbose_name = '记录'
        verbose_name_plural = '记录'
    
    def __str__(self):
        return f"Record-{self.id}"
    
    def clean(self):
        """数据校验"""
        if self.record_data:
            try:
                if isinstance(self.record_data, str):
                    json.loads(self.record_data)
            except json.JSONDecodeError:
                raise ValidationError({'record_data': 'Invalid JSON format'})


class Execution(models.Model):
    """执行表"""
    
    iteration = models.IntegerField(null=True, blank=True, help_text='迭代次数')
    record = models.ForeignKey(
        Record, 
        on_delete=models.RESTRICT, 
        related_name='executions',
        help_text='记录ID'
    )
    
    class Meta:
        db_table = 'Execution'
        verbose_name = '执行'
        verbose_name_plural = '执行'
    
    def __str__(self):
        return f"Execution-{self.id} (Iteration: {self.iteration})"
    
    def clean(self):
        """数据校验"""
        if self.record_id and not Record.objects.filter(id=self.record_id).exists():
            raise ValidationError({'record': 'Referenced Record does not exist'})
        if self.iteration is not None and self.iteration < 0:
            raise ValidationError({'iteration': 'Iteration must be non-negative'})


class AnalysisAlgorithm(models.Model):
    """分析表"""
    
    id = models.AutoField(primary_key=True)  # 显式定义自增主键
    name = models.CharField(max_length=50, null=True, blank=True, help_text='分析算法')
    parameters = models.TextField(null=True, blank=True, help_text='分析（公式）参数')
    
    class Meta:
        db_table = 'AnalysisAlgorithm'
        verbose_name = '分析算法'
        verbose_name_plural = '分析算法'
    
    def __str__(self):
        return f"{self.name or f'Algorithm-{self.id}'}"


class FormatConversion(models.Model):
    """格式转换表"""
    
    input_format = models.CharField(max_length=50, null=True, blank=True, help_text='输入格式')
    output_format = models.CharField(max_length=50, null=True, blank=True, help_text='输出格式')
    
    class Meta:
        db_table = 'FormatConvertion'
        verbose_name = '格式转换'
        verbose_name_plural = '格式转换'
    
    def __str__(self):
        return f"{self.input_format} -> {self.output_format}"


class Result(models.Model):
    """返回结果表"""
    
    analysis_algorithm = models.ForeignKey(
        AnalysisAlgorithm, 
        on_delete=models.RESTRICT, 
        related_name='results',
        help_text='分析算法ID'
    )
    format_conversion = models.ForeignKey(
        FormatConversion, 
        on_delete=models.RESTRICT, 
        related_name='results',
        help_text='格式转换ID'
    )
    
    class Meta:
        db_table = 'Result'
        verbose_name = '结果'
        verbose_name_plural = '结果'
    
    def __str__(self):
        return f"Result-{self.id}"
    
    def clean(self):
        """数据校验"""
        if self.analysis_algorithm_id and not AnalysisAlgorithm.objects.filter(id=self.analysis_algorithm_id).exists():
            raise ValidationError({'analysis_algorithm': 'Referenced AnalysisAlgorithm does not exist'})
        if self.format_conversion_id and not FormatConversion.objects.filter(id=self.format_conversion_id).exists():
            raise ValidationError({'format_conversion': 'Referenced FormatConversion does not exist'})


class Simulation(models.Model):
    """仿真表"""
    
    condition = models.ForeignKey(
        Condition, 
        on_delete=models.RESTRICT, 
        related_name='simulations',
        help_text='条件ID'
    )
    execution = models.ForeignKey(
        Execution, 
        on_delete=models.RESTRICT, 
        related_name='simulations',
        help_text='执行ID'
    )
    result = models.ForeignKey(
        Result, 
        on_delete=models.RESTRICT, 
        related_name='simulations',
        help_text='结果ID'
    )
    
    class Meta:
        db_table = 'Simulation'
        verbose_name = '仿真'
        verbose_name_plural = '仿真'
    
    def __str__(self):
        return f"Simulation-{self.id}"
    
    def clean(self):
        """数据校验"""
        if self.condition_id and not Condition.objects.filter(id=self.condition_id).exists():
            raise ValidationError({'condition': 'Referenced Condition does not exist'})
        if self.execution_id and not Execution.objects.filter(id=self.execution_id).exists():
            raise ValidationError({'execution': 'Referenced Execution does not exist'})
        if self.result_id and not Result.objects.filter(id=self.result_id).exists():
            raise ValidationError({'result': 'Referenced Result does not exist'})


class Project(models.Model):
    """项目表"""
    
    diagram = models.ForeignKey(
        Diagram, 
        on_delete=models.RESTRICT, 
        related_name='projects',
        help_text='图表ID'
    )
    simulation = models.ForeignKey(
        Simulation, 
        on_delete=models.RESTRICT, 
        related_name='projects',
        help_text='仿真ID'
    )
    
    class Meta:
        db_table = 'Project'
        verbose_name = '项目'
        verbose_name_plural = '项目'
    
    def __str__(self):
        return f"Project-{self.id}"
    
    def clean(self):
        """数据校验"""
        if self.diagram_id and not Diagram.objects.filter(id=self.diagram_id).exists():
            raise ValidationError({'diagram': 'Referenced Diagram does not exist'})
        if self.simulation_id and not Simulation.objects.filter(id=self.simulation_id).exists():
            raise ValidationError({'simulation': 'Referenced Simulation does not exist'})


class ResourceImportJob(models.Model):
    IMPORT_TYPE_CHOICES = [
        ('MAP', 'Map全量导入'),
        ('LAYER', 'Layer增量导入')
    ]
    
    import_type = models.CharField(max_length=10, choices=IMPORT_TYPE_CHOICES)
    target_map = models.ForeignKey(Map, null=True, blank=True, 
                                  on_delete=models.CASCADE,
                                  related_name='import_jobs')
    target_layer = models.ForeignKey(Layer, null=True, blank=True,
                                    on_delete=models.CASCADE,
                                    related_name='import_jobs')
    imported_data = models.JSONField(help_text='导入的JSON数据')
    status = models.CharField(max_length=20, default='PENDING', 
                             choices=[('PENDING','待处理'), ('SUCCESS','成功'), ('FAILED','失败')])
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # version_comment = models.TextField(blank=True, help_text='版本提交说明')
    # rollback_point = models.BooleanField(default=False, help_text='是否作为回滚点')

    class Meta:
        verbose_name = '资源导入任务'
        verbose_name_plural = '资源导入任务'

    def __str__(self):
        return f"{self.get_import_type_display()} Import - {self.created_at}"


class MapVersionSnapshot(models.Model):
    from_map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name='from_snapshots')
    to_map = models.ForeignKey(Map, on_delete=models.CASCADE, related_name='to_snapshots')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'MapVersionSnapshot'
        verbose_name = '地图版本快照'
        verbose_name_plural = '地图版本快照'
    
    def __str__(self):
        return f"Snapshot {self.id}: Map {self.from_map_id} -> {self.to_map_id}"

# Add this after the Map model definition