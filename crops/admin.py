from django.contrib import admin
from .models import Crop, CropVariable, PredictedData

@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('crop_name', 'unit', 'grow_duration')
    search_fields = ('crop_name',)
    list_filter = ('grow_duration',)
    ordering = ('crop_name',)

@admin.register(CropVariable)
class CropVariableAdmin(admin.ModelAdmin):
    list_display = ('crop', 'date', 'average_price', 'min_price', 'max_price', 'file_name')
    list_filter = ('crop', 'date')  # สามารถกรองตามชนิดพืชและวันที่
    search_fields = ('crop__crop_name', 'file_name')  # ค้นหาจากชื่อพืช (FK) และชื่อไฟล์
    ordering = ('-date',)  # เรียงลำดับจากวันที่ล่าสุดไปหาเก่าสุด

@admin.register(PredictedData)
class PredictedDataAdmin(admin.ModelAdmin):
    list_display = ('crop', 'predicted_date', 'predicted_price')
    list_filter = ('crop', 'predicted_date')
    search_fields = ('crop__crop_name',)
    ordering = ('-predicted_date',)
