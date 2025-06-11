from django.contrib import admin
from .models import ResourceImportJob

@admin.register(ResourceImportJob)
class ResourceImportJobAdmin(admin.ModelAdmin):
    """资源导入任务后台管理"""
    
    list_display = ['id', 'import_type', 'target_id', 'status', 'created_at']
    list_filter = ['import_type', 'status', 'created_at']
    search_fields = ['target_id', 'log']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('基本信息', {
            'fields': ('import_type', 'target_id', 'status')
        }),
        ('日志与时间', {
            'fields': ('log', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
