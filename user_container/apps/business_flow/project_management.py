from django.shortcuts import get_object_or_404
from ..resourcedb.models import Project, Map, Layer

def create_project(map_id, layer_ids, task_modes):
    """独立的项目创建逻辑"""
    # 参数校验
    if not all([map_id, layer_ids, task_modes]):
        raise ValueError("缺少必要参数：map_id, layer_ids, task_modes")
    
    # 创建Project并关联资源
    project = Project.objects.create(
        name=f"项目_{map_id}_{'-'.join(layer_ids)}",
        task_modes=task_modes,
        map=get_object_or_404(Map, id=map_id)
    )
    project.layers.set(Layer.objects.filter(id__in=layer_ids))
    return project