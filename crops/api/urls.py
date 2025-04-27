from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    CropViewSet, 
    CropVariableViewSet, 
    PredictedDataViewSet,
    crops_list, 
    combined_price_forecast
)
from .export_excel import export_price_data_excel
from .crop_info_list import all_vegetable_info  # Import view จาก crop_info_list.py
from django.conf import settings
from django.conf.urls.static import static
from .quarterly_avg_api import quarterly_avg_data

# Router สำหรับ API endpoints
router = DefaultRouter()
router.register(r'crops', CropViewSet)
router.register(r'crop-variables', CropVariableViewSet)
router.register(r'predicted-data', PredictedDataViewSet)

# กำหนด URL สำหรับ API
urlpatterns = [
    path('api/', include(router.urls)),  # ใช้ router สำหรับ API
    path('api/crops-list/', crops_list, name='crops_list'),  # รายชื่อผัก
    path('api/combined-priceforecast/', combined_price_forecast, name='combined_price_forecast'),  # คำนวณราคาพืช
    path('api/export-excel/', export_price_data_excel, name='export_excel'),  # ส่งออก Excel
    path('api/crop-info-list/', all_vegetable_info, name='crop_info_list'),  # ข้อมูลผักทั้งหมด
    path('api/quarterly-avg/', quarterly_avg_data, name='quarterly_avg'),  # ข้อมูลเฉลี่ยรายไตรมาส
]

# เพิ่ม static file handling ใน DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
