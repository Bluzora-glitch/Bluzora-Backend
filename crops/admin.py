from django.contrib import admin
from .models import Crop, CropVariable, PredictedData, CropModelMapping

class CropModelMappingInline(admin.StackedInline):
    model = CropModelMapping
    can_delete = False
    extra = 1       # แสดงฟอร์มเปล่า 1 ฟอร์ม (กรณียังไม่มีข้อมูล)
    max_num = 1     # จำกัดให้มีได้เพียง 1 รายการ (One-to-One)

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('crop_name', 'unit', 'get_growth_duration_display')
    search_fields = ('crop_name',)
    list_filter = ('min_growth_duration', 'max_growth_duration')
    ordering = ('crop_name',)
    inlines = [CropModelMappingInline]

@admin.register(CropVariable)
class CropVariableAdmin(admin.ModelAdmin):
    list_display = ('crop', 'date', 'average_price', 'min_price', 'max_price', 'file_name')
    list_filter = ('crop', 'date')
    search_fields = ('crop__crop_name', 'file_name')
    ordering = ('-date',)

@admin.register(PredictedData)
class PredictedDataAdmin(admin.ModelAdmin):
    list_display = ('crop', 'predicted_date', 'predicted_price')
    list_filter = ('crop', 'predicted_date')
    search_fields = ('crop__crop_name',)
    ordering = ('-predicted_date',)
