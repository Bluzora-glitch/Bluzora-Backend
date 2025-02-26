from django.contrib import admin
from .models import Crop, CropVariable

class CropVariableAdmin(admin.ModelAdmin):
    list_display = ('crop', 'date', 'average_price', 'min_price', 'max_price')
    list_filter = ('crop',)  # ✅ เพิ่ม filter ตามชนิดพืช
    search_fields = ('crop__crop_name',)  # ✅ เพิ่มช่องค้นหาพืชตามชื่อ

admin.site.register(Crop)
admin.site.register(CropVariable, CropVariableAdmin)
